import os
import torch
import numpy as np
from PIL import Image, ImageOps, ImageSequence
import folder_paths
import comfy.model_management
import node_helpers

class PMS_LoadImageSequenceFromFolder:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "directory_path": ("STRING", {"default": ""}),
                "index": ("INT", {"default": 0, "min": 0, "max": 1000000, "step": 1, "control_after_generate": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("IMAGE", "MASK", "filename")
    FUNCTION = "load_image"
    CATEGORY = "image"

    def load_image(self, directory_path, index):
        # Fallback to ComfyUI input directory if empty or invalid
        if not directory_path or not os.path.isdir(directory_path):
            print(f"Warning: Directory '{directory_path}' not found. Falling back to default ComfyUI input folder.")
            directory_path = folder_paths.get_input_directory()

        image_files = []
        if os.path.isdir(directory_path):
            # List files in directory
            files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
            # Filter image files
            valid_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif']
            image_files = [f for f in files if os.path.splitext(f)[1].lower() in valid_extensions]
            image_files.sort()  # Sort alphabetically

        if not image_files:
            print(f"Warning: No valid images found in '{directory_path}'. Returning a black dummy image.")
            device = comfy.model_management.intermediate_device()
            dtype = comfy.model_management.intermediate_dtype()
            dummy_image = torch.zeros((1, 512, 512, 3), dtype=dtype, device=device)
            dummy_mask = torch.zeros((1, 512, 512), dtype=dtype, device=device)
            return (dummy_image, dummy_mask, "no_images_found.png")

        # Calculate actual index using modulo
        actual_index = index % len(image_files)
        image_name = image_files[actual_index]
        image_path = os.path.join(directory_path, image_name)

        # Load image using PIL
        img = node_helpers.pillow(Image.open, image_path)
        
        dtype = comfy.model_management.intermediate_dtype()
        device = comfy.model_management.intermediate_device()

        output_images = []
        output_masks = []
        w, h = None, None

        for i in ImageSequence.Iterator(img):
            i = node_helpers.pillow(ImageOps.exif_transpose, i)
            image = i.convert("RGB")

            if len(output_images) == 0:
                w = image.size[0]
                h = image.size[1]

            if image.size[0] != w or image.size[1] != h:
                continue

            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            output_images.append(image.to(dtype=dtype))
            output_masks.append(mask.unsqueeze(0).to(dtype=dtype))

        output_image = torch.cat(output_images, dim=0)
        output_mask = torch.cat(output_masks, dim=0)

        return (output_image.to(device=device, dtype=dtype), output_mask.to(device=device, dtype=dtype), image_name)

    @classmethod
    def IS_CHANGED(s, directory_path, index):
        if os.path.isdir(directory_path):
            files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
            valid_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif']
            image_files = [f for f in files if os.path.splitext(f)[1].lower() in valid_extensions]
            image_files.sort()
            if image_files:
                actual_index = index % len(image_files)
                image_name = image_files[actual_index]
                image_path = os.path.join(directory_path, image_name)
                if os.path.exists(image_path):
                    return f"{image_path}_{os.path.getmtime(image_path)}_{index}"
        return f"{directory_path}_{index}"
