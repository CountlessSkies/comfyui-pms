class PMS_SwitchCase:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "select": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
            },
            "optional": {
                "input_1": ("*",),
                "input_2": ("*",),
                "input_3": ("*",),
                "input_4": ("*",),
                "input_5": ("*",),
                "input_6": ("*",),
                "input_7": ("*",),
                "input_8": ("*",),
                "input_9": ("*",),
                "input_10": ("*",),
            }
        }

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("selected_value",)
    FUNCTION = "route"
    CATEGORY = "utils"

    def route(self, select, **kwargs):
        key = f"input_{select}"
        val = kwargs.get(key, None)
        return (val,)
