from .image_resize_by_height import PMS_ImageResizeByReferenceHeight
from .image_crop_closest_ratio import PMS_ImageCropToClosestAspectRatio
from .transparent_png_creator import PMS_TransparentPNGFromMask

NODE_CLASS_MAPPINGS = {
    "PMS_ImageResizeByReferenceHeight": PMS_ImageResizeByReferenceHeight,
    "PMS_ImageCropToClosestAspectRatio": PMS_ImageCropToClosestAspectRatio,
    "PMS_TransparentPNGFromMask": PMS_TransparentPNGFromMask,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PMS_ImageResizeByReferenceHeight": "PMS Image Resize by Reference Height",
    "PMS_ImageCropToClosestAspectRatio": "PMS Image Crop to Closest Aspect Ratio",
    "PMS_TransparentPNGFromMask": "PMS Transparent PNG From Mask",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
