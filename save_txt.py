import os
import datetime
import time

class PMS_SaveTXT:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {"default": ""}),
                "filename": ("STRING", {"default": "output.txt"}),
                "save_mode": (["Overwrite", "Increment", "Timestamp"], {"default": "Increment"}),
            },
            "optional": {
                "text": ("STRING", {"default": "", "multiline": True}),
                "any_data": ("*",),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_txt"
    CATEGORY = "pms/utils"
    OUTPUT_NODE = True

    def save_txt(self, directory_path, filename, save_mode="Overwrite", text="", any_data=None):
        if not directory_path:
            import folder_paths
            directory_path = folder_paths.get_output_directory()

        if not os.path.isdir(directory_path):
            os.makedirs(directory_path, exist_ok=True)

        # Determine the content to save
        content_to_save = ""
        if any_data is not None:
            if isinstance(any_data, list):
                # If it's a list, join elements with newlines
                content_to_save = "\n".join(str(item) for item in any_data)
            else:
                content_to_save = str(any_data)
        else:
            content_to_save = text

        # Handle filename based on save_mode
        base_name, ext = os.path.splitext(filename)
        if not ext:
            ext = ".txt"

        if save_mode == "Timestamp":
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            final_filename = f"{base_name}_{timestamp}{ext}"
        elif save_mode == "Increment":
            counter = 1
            final_filename = f"{base_name}_{counter}{ext}"
            while os.path.exists(os.path.join(directory_path, final_filename)):
                counter += 1
                final_filename = f"{base_name}_{counter}{ext}"
        else:  # Overwrite
            final_filename = f"{base_name}{ext}"

        file_path = os.path.join(directory_path, final_filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content_to_save)

        return {}

    @classmethod
    def IS_CHANGED(s, directory_path, filename, save_mode="Overwrite", text="", any_data=None):
        return time.time()
