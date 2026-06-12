import torch

class PMS_ImageCropToClosestAspectRatio:
    crop_positions = [
        "center",
        "top",
        "bottom",
        "left",
        "right",
        "top_left",
        "top_right",
        "bottom_left",
        "bottom_right"
    ]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "crop_position": (s.crop_positions, {"default": "center"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "aspect_ratio_str")
    FUNCTION = "crop"
    CATEGORY = "image/cropping"

    def crop(self, image, crop_position):
        # image shape: [B, H, W, C]
        _, h, w, _ = image.shape
        current_ratio = w / h

        ratios = [
            ("1:1", 1.0),
            ("3:2", 1.5),
            ("2:3", 2.0 / 3.0),
            ("3:4", 3.0 / 4.0),
            ("4:3", 4.0 / 3.0),
            ("4:5", 4.0 / 5.0),
            ("5:4", 5.0 / 4.0),
            ("9:16", 9.0 / 16.0),
            ("16:9", 16.0 / 9.0),
            ("21:9", 21.0 / 9.0),
        ]

        # Find the ratio with the minimum absolute difference
        best_name, best_ratio = min(ratios, key=lambda x: abs(current_ratio - x[1]))

        # Calculate new width and height based on the best ratio
        if current_ratio > best_ratio:
            # Current image is wider than the target ratio -> crop width
            new_h = h
            new_w = min(w, round(h * best_ratio))
        else:
            # Current image is taller than the target ratio -> crop height
            new_w = w
            new_h = min(h, round(w / best_ratio))

        # Determine x_start (horizontal cropping)
        if "left" in crop_position:
            x_start = 0
        elif "right" in crop_position:
            x_start = w - new_w
        else:
            x_start = (w - new_w) // 2

        # Determine y_start (vertical cropping)
        if "top" in crop_position:
            y_start = 0
        elif "bottom" in crop_position:
            y_start = h - new_h
        else:
            y_start = (h - new_h) // 2

        x_end = x_start + new_w
        y_end = y_start + new_h

        # Prevent out of bounds
        x_start = max(0, min(x_start, w - new_w))
        y_start = max(0, min(y_start, h - new_h))
        x_end = min(x_end, w)
        y_end = min(y_end, h)

        cropped_image = image[:, y_start:y_end, x_start:x_end, :]

        return (cropped_image, best_name)
