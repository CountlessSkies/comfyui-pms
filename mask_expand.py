import torch

class PMS_MaskExpand:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "expand": ("INT", {"default": 2, "min": -100, "max": 100, "step": 1}),
                "shape": (["circle", "square", "diamond"], {"default": "circle"}),
            }
        }

    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("mask",)
    FUNCTION = "expand_mask"
    CATEGORY = "image/mask"

    def expand_mask(self, mask, expand, shape):
        if expand == 0:
            return (mask.clone(),)

        # Ensure mask is 3D: [B, H, W]
        is_2d = False
        if len(mask.shape) == 2:
            mask = mask.unsqueeze(0)
            is_2d = True
        elif len(mask.shape) == 4:
            # If [B, C, H, W] and C=1, squeeze it
            if mask.shape[1] == 1:
                mask = mask.squeeze(1)
            else:
                mask = mask.mean(dim=1)

        B, H, W = mask.shape
        device = mask.device
        dtype = mask.dtype
        
        r = abs(expand)
        is_erosion = expand < 0

        # For "square" shape, we can use fast native max_pool2d
        if shape == "square":
            # max_pool2d expects [B, C, H, W]
            mask_4d = mask.unsqueeze(1)
            if not is_erosion:
                # Dilation
                out_4d = torch.nn.functional.max_pool2d(
                    mask_4d, 
                    kernel_size=2*r+1, 
                    stride=1, 
                    padding=r
                )
            else:
                # Erosion: min(x) = -max(-x)
                out_4d = -torch.nn.functional.max_pool2d(
                    -mask_4d, 
                    kernel_size=2*r+1, 
                    stride=1, 
                    padding=r
                )
            out = out_4d.squeeze(1)
        else:
            # Generate structuring element (kernel)
            # Coordinates from -r to r
            y, x = torch.meshgrid(
                torch.arange(-r, r + 1, device=device),
                torch.arange(-r, r + 1, device=device),
                indexing='ij'
            )
            
            if shape == "circle":
                # Circle structuring element (Euclidean distance <= r)
                # We use r**2 + 0.5 to avoid boundary rounding artifacts and matching cross shape at r=1
                kernel = (x**2 + y**2) <= (r**2 + 0.5)
            elif shape == "diamond":
                # Diamond structuring element (Manhattan distance <= r)
                kernel = (torch.abs(x) + torch.abs(y)) <= r
            else:
                # Fallback to square if anything else
                kernel = torch.ones((2*r+1, 2*r+1), dtype=torch.bool, device=device)

            # We process using chunking along the height dimension to prevent OOM
            # on large inputs.
            mask_4d = mask.unsqueeze(1) # [B, 1, H, W]
            out_4d = self._process_non_square_chunks(mask_4d, r, kernel, is_erosion)
            out = out_4d.squeeze(1)

        # Restore 2D shape if input was 2D
        if is_2d:
            out = out.squeeze(0)

        return (out.to(dtype=dtype),)

    def _process_non_square_chunks(self, mask_4d, r, kernel, is_erosion):
        B, C, H, W = mask_4d.shape
        kernel_pixels = (2 * r + 1) ** 2
        
        # We target a max of 50 million elements in the unfolded tensor per chunk.
        # This keeps the memory usage for the unfold operation very small (under ~200MB).
        max_pixels_per_chunk = 50_000_000 // kernel_pixels
        chunk_h = max(1, max_pixels_per_chunk // W)
        
        if chunk_h >= H:
            return self._process_single_chunk(mask_4d, r, kernel, is_erosion)
            
        out_chunks = []
        for i in range(0, H, chunk_h):
            start_y = max(0, i - r)
            end_y = min(H, i + chunk_h + r)
            
            chunk = mask_4d[:, :, start_y:end_y, :]
            
            # Determine padding needed at boundaries
            pad_top = r if start_y == 0 else 0
            pad_bottom = r if end_y == H else 0
            
            # Pad height and width
            chunk_padded = torch.nn.functional.pad(
                chunk, 
                (r, r, pad_top, pad_bottom), 
                mode='replicate'
            )
            
            # Perform morphology on the padded chunk
            processed_chunk = self._apply_unfold_morphology(chunk_padded, r, kernel, is_erosion)
            
            # Extract target rows corresponding to this chunk's non-overlapping range
            target_len = min(H, i + chunk_h) - i
            
            sliced_chunk = processed_chunk[:, :, :target_len, :]
            out_chunks.append(sliced_chunk)
            
        return torch.cat(out_chunks, dim=2)

    def _process_single_chunk(self, mask_4d, r, kernel, is_erosion):
        # Full replicate padding on all sides
        padded = torch.nn.functional.pad(mask_4d, (r, r, r, r), mode='replicate')
        return self._apply_unfold_morphology(padded, r, kernel, is_erosion)

    def _apply_unfold_morphology(self, padded, r, kernel, is_erosion):
        # padded: [B, 1, H_pad, W_pad]
        # Unfold extracts patch values for each pixel
        patches = padded.unfold(2, 2*r+1, 1).unfold(3, 2*r+1, 1)
        # patches: [B, 1, H, W, 2r+1, 2r+1]
        
        kernel_expanded = kernel.view(1, 1, 1, 1, 2*r+1, 2*r+1)
        
        if not is_erosion:
            # Dilation: Max value where kernel is True (ignore False parts by setting to -999.0)
            masked_patches = torch.where(kernel_expanded, patches, -999.0)
            return masked_patches.amax(dim=(-2, -1))
        else:
            # Erosion: Min value where kernel is True (ignore False parts by setting to 999.0)
            masked_patches = torch.where(kernel_expanded, patches, 999.0)
            return masked_patches.amin(dim=(-2, -1))
