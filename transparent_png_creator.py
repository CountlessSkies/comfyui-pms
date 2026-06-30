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
                "padding": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
                "invert_mask": ("BOOLEAN", {"default": False}),
                "resize_source": (["mask_to_image", "image_to_mask", "none"], {"default": "mask_to_image"}),
                "reference_by": (["height", "width"], {"default": "height"}),
                "resize_mode": (["keep_aspect_ratio", "match_reference_dimensions", "stretch_to_reference"], {"default": "keep_aspect_ratio"}),
                "alignment": ([
                    "top-left", "top-center", "top-right",
                    "middle-left", "middle-center", "middle-right",
                    "bottom-left", "bottom-center", "bottom-right"
                ], {"default": "middle-center"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "create_png"
    CATEGORY = "image/process"

    def create_png(self, image, mask, trim_to_mask, padding, invert_mask, 
                   resize_source="mask_to_image", reference_by="height", 
                   resize_mode="keep_aspect_ratio", alignment="middle-center"):
        
        def align_and_fit(tensor, final_h, final_w, align="middle-center", is_image=False):
            if is_image:
                B_t, curr_h, curr_w, C_t = tensor.shape
                x = tensor.movedim(-1, 1) # [B, C, curr_h, curr_w]
            else:
                B_t, curr_h, curr_w = tensor.shape
                x = tensor.unsqueeze(1) # [B, 1, curr_h, curr_w]
                
            pad_left = pad_right = pad_top = pad_bottom = 0
            crop_left = crop_right = crop_top = crop_bottom = 0
            
            v_align, h_align = align.split("-")
            
            if curr_w < final_w:
                diff = final_w - curr_w
                if h_align == "left":
                    pad_left = 0
                    pad_right = diff
                elif h_align == "center":
                    pad_left = diff // 2
                    pad_right = diff - pad_left
                else: # right
                    pad_left = diff
                    pad_right = 0
            elif curr_w > final_w:
                diff = curr_w - final_w
                if h_align == "left":
                    crop_left = 0
                    crop_right = diff
                elif h_align == "center":
                    crop_left = diff // 2
                    crop_right = diff - crop_left
                else: # right
                    crop_left = diff
                    crop_right = 0
                    
            if curr_h < final_h:
                diff = final_h - curr_h
                if v_align == "top":
                    pad_top = 0
                    pad_bottom = diff
                elif v_align == "middle":
                    pad_top = diff // 2
                    pad_bottom = diff - pad_top
                else: # bottom
                    pad_top = diff
                    pad_bottom = 0
            elif curr_h > final_h:
                diff = curr_h - final_h
                if v_align == "top":
                    crop_top = 0
                    crop_bottom = diff
                elif v_align == "middle":
                    crop_top = diff // 2
                    crop_bottom = diff - crop_top
                else: # bottom
                    crop_top = diff
                    crop_bottom = 0
                    
            if crop_left > 0 or crop_right > 0 or crop_top > 0 or crop_bottom > 0:
                x = x[:, :, crop_top:curr_h-crop_bottom, crop_left:curr_w-crop_right]
                
            if pad_left > 0 or pad_right > 0 or pad_top > 0 or pad_bottom > 0:
                x = torch.nn.functional.pad(x, (pad_left, pad_right, pad_top, pad_bottom), mode='constant', value=0.0)
                
            if is_image:
                return x.movedim(1, -1)
            else:
                return x.squeeze(1)

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
        if resize_source == "mask_to_image":
            if resize_mode == "match_reference_dimensions":
                target_height = H
                target_width = W
            elif reference_by == "height":
                target_height = H
                if resize_mode == "keep_aspect_ratio":
                    target_width = max(1, round(W_mask * H / H_mask))
                else: # stretch_to_reference
                    target_width = W_mask
            else: # reference_by == "width"
                target_width = W
                if resize_mode == "keep_aspect_ratio":
                    target_height = max(1, round(H_mask * W / W_mask))
                else: # stretch_to_reference
                    target_height = H_mask
            
            mask_temp = mask.unsqueeze(1)
            mask_temp = torch.nn.functional.interpolate(mask_temp, size=(target_height, target_width), mode='bilinear', align_corners=False)
            mask = mask_temp.squeeze(1)
            
            if (target_height != H) or (target_width != W):
                mask = align_and_fit(mask, H, W, alignment, is_image=False)
                
            H_mask, W_mask = H, W

        elif resize_source == "image_to_mask":
            if resize_mode == "match_reference_dimensions":
                target_height = H_mask
                target_width = W_mask
            elif reference_by == "height":
                target_height = H_mask
                if resize_mode == "keep_aspect_ratio":
                    target_width = max(1, round(W * H_mask / H))
                else: # stretch_to_reference
                    target_width = W
            else: # reference_by == "width"
                target_width = W_mask
                if resize_mode == "keep_aspect_ratio":
                    target_height = max(1, round(H * W_mask / W))
                else: # stretch_to_reference
                    target_height = H
            
            image_temp = image.movedim(-1, 1)
            image_temp = torch.nn.functional.interpolate(image_temp, size=(target_height, target_width), mode='bilinear', align_corners=False)
            image = image_temp.movedim(1, -1)
            
            if (target_height != H_mask) or (target_width != W_mask):
                image = align_and_fit(image, H_mask, W_mask, alignment, is_image=True)
                
            H, W = H_mask, W_mask
            
        elif resize_source == "none":
            # Fallback to prevent crash if dimensions still do not match
            if (H != H_mask) or (W != W_mask):
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
            threshold = 0.05
            non_zero_coords = (mask > threshold).nonzero()
            
            if non_zero_coords.size(0) > 0:
                y_indices = non_zero_coords[:, 1]
                x_indices = non_zero_coords[:, 2]
                
                y_min = int(y_indices.min().item())
                y_max = int(y_indices.max().item())
                x_min = int(x_indices.min().item())
                x_max = int(x_indices.max().item())
                
                y_min = max(0, y_min - padding)
                y_max = min(H - 1, y_max + padding)
                x_min = max(0, x_min - padding)
                x_max = min(W - 1, x_max + padding)
                
                if y_max > y_min and x_max > x_min:
                    rgba = rgba[:, y_min:y_max+1, x_min:x_max+1, :]
                    mask = mask[:, y_min:y_max+1, x_min:x_max+1]
            else:
                rgba = torch.zeros((B, 8, 8, 4), dtype=rgba.dtype, device=rgba.device)
                mask = torch.zeros((B, 8, 8), dtype=mask.dtype, device=mask.device)
        
        return (rgba, mask)
