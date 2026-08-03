import torch
import comfy.utils

class PMS_ImageResizeByReference:
    upscale_methods = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]
    reference_options = ["height", "width"]
    resize_modes = ["keep_aspect_ratio", "match_reference_dimensions"]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "reference_image": ("IMAGE",),
                "upscale_method": (s.upscale_methods, {"default": "bilinear"}),
                "reference_by": (s.reference_options, {"default": "height"}),
                "resize_mode": (s.resize_modes, {"default": "keep_aspect_ratio"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "resize"
    CATEGORY = "image/upscaling"

    def resize(self, image, reference_image, upscale_method, reference_by, resize_mode):
        # image has shape [B, H, W, C]
        # reference_image has shape [B_ref, H_ref, W_ref, C_ref]
        
        # Determine reference dimensions
        ref_height = reference_image.shape[1]
        ref_width = reference_image.shape[2]
        
        # Transpose image to [B, C, H, W] for scaling
        samples = image.movedim(-1, 1)
        original_height = samples.shape[2]
        original_width = samples.shape[3]
        
        if resize_mode == "match_reference_dimensions":
            target_width = ref_width
            target_height = ref_height
        elif reference_by == "height":
            target_height = ref_height
            target_width = max(1, round(original_width * target_height / original_height))
        else: # reference_by == "width"
            target_width = ref_width
            target_height = max(1, round(original_height * target_width / original_width))
            
        s = comfy.utils.common_upscale(samples, target_width, target_height, upscale_method, "disabled")
        s = s.movedim(1, -1)
        return (s,)
