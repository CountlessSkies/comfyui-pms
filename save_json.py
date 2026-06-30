import os
import json
import datetime
import time

class PMS_SaveJSON:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {"default": ""}),
                "filename": ("STRING", {"default": "output.json"}),
                "save_mode": (["Overwrite", "Increment", "Timestamp"], {"default": "Increment"}),
            },
            "optional": {
                "json_text": ("STRING", {"default": "", "multiline": True}),
                "any_data": ("*",),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_json"
    CATEGORY = "pms/utils"
    OUTPUT_NODE = True

    def save_json(self, directory_path, filename, save_mode="Overwrite", json_text="", any_data=None):
        if not directory_path:
            # Fallback to comfy input/output directory if empty
            import folder_paths
            directory_path = folder_paths.get_output_directory()

        if not os.path.isdir(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            
        data_to_save = None
        
        # Determine what data to save
        if any_data is not None:
            if isinstance(any_data, (dict, list, str, int, float, bool)):
                data_to_save = any_data
            else:
                # Try to serialize or convert to string
                try:
                    data_to_save = str(any_data)
                except Exception as e:
                    data_to_save = f"Unserializable object: {type(any_data)}"
        else:
            data_to_save = json_text

        # Try parsing string as JSON if it is a string
        if isinstance(data_to_save, str):
            try:
                data_to_save = json.loads(data_to_save)
            except json.JSONDecodeError:
                # If it's not valid JSON, we'll write it as a raw string
                pass

        # Handle filename based on save_mode
        base_name, ext = os.path.splitext(filename)
        if not ext:
            ext = ".json"

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
            if isinstance(data_to_save, (dict, list)):
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            else:
                try:
                    f.write(str(data_to_save))
                except Exception as e:
                    json.dump({"error": str(e), "raw_data": str(data_to_save)}, f, indent=4)

        return {}

    @classmethod
    def IS_CHANGED(s, directory_path, filename, save_mode="Overwrite", json_text="", any_data=None):
        # Always run to ensure files are saved properly on every execution
        return time.time()
