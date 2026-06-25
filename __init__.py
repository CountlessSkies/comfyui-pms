from .image_resize_by_height import PMS_ImageResizeByReferenceHeight
from .image_crop_closest_ratio import PMS_ImageCropToClosestAspectRatio
from .transparent_png_creator import PMS_TransparentPNGFromMask
from .switch_case import PMS_SwitchCase
from .mask_expand import PMS_MaskExpand

NODE_CLASS_MAPPINGS = {
    "PMS_ImageResizeByReferenceHeight": PMS_ImageResizeByReferenceHeight,
    "PMS_ImageCropToClosestAspectRatio": PMS_ImageCropToClosestAspectRatio,
    "PMS_TransparentPNGFromMask": PMS_TransparentPNGFromMask,
    "PMS_SwitchCase": PMS_SwitchCase,
    "PMS_MaskExpand": PMS_MaskExpand,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PMS_ImageResizeByReferenceHeight": "PMS Image Resize by Reference Height",
    "PMS_ImageCropToClosestAspectRatio": "PMS Image Crop to Closest Aspect Ratio",
    "PMS_TransparentPNGFromMask": "PMS Transparent PNG From Mask",
    "PMS_SwitchCase": "PMS Switch Case",
    "PMS_MaskExpand": "PMS Mask Expand",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
