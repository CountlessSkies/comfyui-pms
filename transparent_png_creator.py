import torch

class PMS_TransparentPNGFromMask:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "trim_to_mask": ("BOOLEAN", {"default": False}),
                "padding": ("INT", {"default": 10, "min": 0, "max": 1000, "step": 1}),
                "invert_mask": ("BOOLEAN", {"default": False}),
                "resize_mode": (["scale_mask_to_image", "scale_image_to_mask", "none"], {
                    "default": "scale_mask_to_image"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "create_png"
    CATEGORY = "image/process"

    def create_png(self, image, mask, trim_to_mask, padding, invert_mask, resize_mode="scale_mask_to_image"):
        # Ensure image has batch dimension [B, H, W, C]
        if len(image.shape) == 3:
            image = image.unsqueeze(0)
            
        B, H, W, C = image.shape
        
        # Ensure mask is [B, H, W]
        if len(mask.shape) == 2:
            mask = mask.unsqueeze(0)
        
        # Clone mask and ensure same device and dtype as image
        mask = mask.clone().to(device=image.device, dtype=image.dtype)
        B_mask, H_mask, W_mask = mask.shape
        
        # Resize mask or image if dimensions do not match
        if (H != H_mask) or (W != W_mask):
            if resize_mode == "scale_mask_to_image":
                # Scale mask to match image dimensions [B_mask, 1, H_mask, W_mask]
                mask_temp = mask.unsqueeze(1)
                mask_temp = torch.nn.functional.interpolate(mask_temp, size=(H, W), mode='bilinear', align_corners=False)
                mask = mask_temp.squeeze(1)
                H_mask, W_mask = H, W
            elif resize_mode == "scale_image_to_mask":
                # Scale image to match mask dimensions
                # PyTorch interpolate expects [B, C, H, W], image is [B, H, W, C]
                image_temp = image.permute(0, 3, 1, 2)
                image_temp = torch.nn.functional.interpolate(image_temp, size=(H_mask, W_mask), mode='bilinear', align_corners=False)
                image = image_temp.permute(0, 2, 3, 1)
                H, W = H_mask, W_mask
            elif resize_mode == "none":
                # Fallback to prevent crash, print warning
                print(f"Warning: Image size ({W}x{H}) and Mask size ({W_mask}x{H_mask}) mismatch. Fallback: scaling mask to image.")
                mask_temp = mask.unsqueeze(1)
                mask_temp = torch.nn.functional.interpolate(mask_temp, size=(H, W), mode='bilinear', align_corners=False)
                mask = mask_temp.squeeze(1)
                H_mask, W_mask = H, W
        
        # If mask batch size doesn't match image batch size, align them
        if mask.shape[0] != B:
            if mask.shape[0] == 1:
                mask = mask.expand(B, -1, -1)
            elif B == 1:
                image = image.expand(mask.shape[0], -1, -1, -1)
                B = image.shape[0]
            else:
                min_b = min(B, mask.shape[0])
                image = image[:min_b]
                mask = mask[:min_b]
                B = min_b

        # Apply invert_mask if requested
        if invert_mask:
            mask = 1.0 - mask

        # Extract RGB (first 3 channels)
        rgb = image[:, :, :, :3]
        
        # Add a channel dimension to the mask: [B, H, W, 1]
        alpha = mask.unsqueeze(-1)
        
        # Concatenate RGB and Alpha to get RGBA [B, H, W, 4]
        rgba = torch.cat((rgb, alpha), dim=-1)
        
        # If trim_to_mask is True, we crop to the bounding box of the mask
        if trim_to_mask:
            # Threshold to filter out noise in the mask (e.g. very dim pixels)
            threshold = 0.05
            non_zero_coords = (mask > threshold).nonzero()
            
            if non_zero_coords.size(0) > 0:
                # non_zero_coords columns: [batch_idx, y, x]
                y_indices = non_zero_coords[:, 1]
                x_indices = non_zero_coords[:, 2]
                
                y_min = int(y_indices.min().item())
                y_max = int(y_indices.max().item())
                x_min = int(x_indices.min().item())
                x_max = int(x_indices.max().item())
                
                # Apply padding, clamping to image bounds
                y_min = max(0, y_min - padding)
                y_max = min(H - 1, y_max + padding)
                x_min = max(0, x_min - padding)
                x_max = min(W - 1, x_max + padding)
                
                # Crop both the RGBA image and the mask
                if y_max > y_min and x_max > x_min:
                    rgba = rgba[:, y_min:y_max+1, x_min:x_max+1, :]
                    mask = mask[:, y_min:y_max+1, x_min:x_max+1]
            else:
                # Fallback: if mask is completely empty, return a small 8x8 transparent image/mask
                rgba = torch.zeros((B, 8, 8, 4), dtype=rgba.dtype, device=rgba.device)
                mask = torch.zeros((B, 8, 8), dtype=mask.dtype, device=mask.device)
        
        return (rgba, mask)
