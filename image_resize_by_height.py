import torch
import comfy.utils

class PMS_ImageResizeByReferenceHeight:
    upscale_methods = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]
    resize_modes = ["keep_aspect_ratio", "match_reference_dimensions", "stretch_height_only"]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "reference_image": ("IMAGE",),
                "upscale_method": (s.upscale_methods, {"default": "bilinear"}),
                "resize_mode": (s.resize_modes, {"default": "keep_aspect_ratio"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "resize"
    CATEGORY = "image/upscaling"

    def resize(self, image, reference_image, upscale_method, resize_mode):
        # image has shape [B, H, W, C]
        # reference_image has shape [B_ref, H_ref, W_ref, C_ref]
        
        # Determine reference height
        target_height = reference_image.shape[1]
        
        # Transpose image to [B, C, H, W] for scaling
        samples = image.movedim(-1, 1)
        original_height = samples.shape[2]
        original_width = samples.shape[3]
        
        if resize_mode == "keep_aspect_ratio":
            target_width = max(1, round(original_width * target_height / original_height))
        elif resize_mode == "match_reference_dimensions":
            target_width = reference_image.shape[2]
        else: # stretch_height_only
            target_width = original_width
            
        s = comfy.utils.common_upscale(samples, target_width, target_height, upscale_method, "disabled")
        s = s.movedim(1, -1)
        return (s,)
