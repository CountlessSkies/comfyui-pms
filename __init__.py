from .image_resize_by_reference import PMS_ImageResizeByReference
from .image_crop_closest_ratio import PMS_ImageCropToClosestAspectRatio
from .transparent_png_creator import PMS_TransparentPNGFromMask
from .switch_case import PMS_SwitchCase
from .mask_expand import PMS_MaskExpand
from .load_images_sequentially import PMS_LoadImageSequenceFromFolder
from .save_json import PMS_SaveJSON
from .save_txt import PMS_SaveTXT

NODE_CLASS_MAPPINGS = {
    "PMS_ImageResizeByReference": PMS_ImageResizeByReference,
    "PMS_ImageCropToClosestAspectRatio": PMS_ImageCropToClosestAspectRatio,
    "PMS_TransparentPNGFromMask": PMS_TransparentPNGFromMask,
    "PMS_SwitchCase": PMS_SwitchCase,
    "PMS_MaskExpand": PMS_MaskExpand,
    "PMS_LoadImageSequenceFromFolder": PMS_LoadImageSequenceFromFolder,
    "PMS_SaveJSON": PMS_SaveJSON,
    "PMS_SaveTXT": PMS_SaveTXT,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PMS_ImageResizeByReference": "PMS Image Resize by Reference",
    "PMS_ImageCropToClosestAspectRatio": "PMS Image Crop to Closest Aspect Ratio",
    "PMS_TransparentPNGFromMask": "PMS Transparent PNG From Mask",
    "PMS_SwitchCase": "PMS Switch Case",
    "PMS_MaskExpand": "PMS Mask Expand",
    "PMS_LoadImageSequenceFromFolder": "PMS Load Image Sequence From Folder",
    "PMS_SaveJSON": "PMS Save JSON",
    "PMS_SaveTXT": "PMS Save TXT",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
