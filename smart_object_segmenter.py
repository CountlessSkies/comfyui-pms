import torch
import numpy as np
from PIL import Image
from safetensors.torch import load_file
import os
import comfy.utils
from transformers import (
    AutoProcessor, 
    AutoModelForZeroShotObjectDetection,
    Sam2ImageProcessor, 
    Sam2Model,
    AutoModelForImageSegmentation
)
from torchvision.transforms import functional as F

class PMS_SmartObjectSegmenter:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"default": "backpack", "multiline": False}),
                "dino_threshold": ("FLOAT", {"default": 0.3, "min": 0.1, "max": 1.0, "step": 0.05}),
                "model_directory": ("STRING", {"default": r"D:\AI\ComfyUI_windows_portable\pms-model"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "segment"
    CATEGORY = "image/segmentation"

    def segment(self, image, prompt, dino_threshold, model_directory):
        # image shape from ComfyUI is [B, H, W, C]
        # We process frame by frame
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        out_images = []
        out_masks = []

        # Grounding DINO config
        dino_repo = "IDEA-Research/grounding-dino-tiny"
        sam_repo = "facebook/sam2-hiera-large"
        birefnet_repo = "ZhengPeng7/BiRefNet"

        # Resolve paths
        sam_path = os.path.join(model_directory, "sam2.1_hiera_large.pt")
        birefnet_path = os.path.join(model_directory, "BiRefNet-general.safetensors.safetensors")

        # Process each image in the batch
        for i in range(image.shape[0]):
            img_tensor = image[i] # [H, W, C]
            # Convert to PIL Image
            img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            img_pil = Image.fromarray(img_np)
            w, h = img_pil.size

            # ==========================================
            # Phase 1: Grounding DINO
            # ==========================================
            dino_processor = AutoProcessor.from_pretrained(dino_repo)
            dino_model = AutoModelForZeroShotObjectDetection.from_pretrained(dino_repo).to(device)

            dino_inputs = dino_processor(images=img_pil, text=prompt + ".", return_tensors="pt").to(device)
            with torch.no_grad():
                dino_outputs = dino_model(**dino_inputs)

            target_sizes = torch.tensor([[h, w]])
            results = dino_processor.post_process_grounded_object_detection(
                dino_outputs, 
                dino_inputs.input_ids, 
                box_threshold=dino_threshold, 
                text_threshold=dino_threshold, 
                target_sizes=target_sizes.to(device)
            )[0]

            boxes = results["boxes"]

            # Unload DINO immediately
            del dino_model
            torch.cuda.empty_cache()

            if len(boxes) == 0:
                # Fallback to full image mask if nothing detected
                fallback_mask = torch.ones((h, w), dtype=torch.float32)
                out_masks.append(fallback_mask)
                rgba_tensor = torch.cat([img_tensor, fallback_mask.unsqueeze(-1)], dim=-1)
                out_images.append(rgba_tensor)
                continue

            # We take the first detected box (or we could combine them)
            # Format: [xmin, ymin, xmax, ymax]
            input_box = boxes[0].tolist()

            # ==========================================
            # Phase 2: SAM 2
            # ==========================================
            sam_processor = Sam2ImageProcessor.from_pretrained(sam_repo)
            sam_model = Sam2Model.from_pretrained(sam_repo)
            
            # Load user's local SAM 2.1 state dict if available
            if os.path.exists(sam_path):
                try:
                    sd = torch.load(sam_path, map_location="cpu")
                    if 'model' in sd:
                        sd = sd['model']
                    sam_model.load_state_dict(sd, strict=False)
                except Exception as e:
                    print(f"[PMS] Warning: Failed to load local SAM weights from {sam_path}: {e}")
            
            sam_model = sam_model.to(device)
            sam_inputs = sam_processor(img_pil, input_boxes=[[input_box]], return_tensors="pt").to(device)
            with torch.no_grad():
                sam_outputs = sam_model(**sam_inputs)

            sam_masks = sam_processor.post_process_masks(
                sam_outputs.pred_masks, sam_inputs.original_sizes, sam_inputs.reshaped_input_sizes
            )

            # Get binary mask from SAM
            best_sam_mask = sam_masks[0][0][0].cpu().numpy().astype(np.uint8) * 255

            # Unload SAM 2
            del sam_model
            torch.cuda.empty_cache()

            # ==========================================
            # Phase 3: BiRefNet
            # ==========================================
            birefnet_model = AutoModelForImageSegmentation.from_pretrained(birefnet_repo, trust_remote_code=True)
            
            # Load user's local BiRefNet state dict if available
            if os.path.exists(birefnet_path):
                try:
                    sd = load_file(birefnet_path, device="cpu")
                    birefnet_model.load_state_dict(sd)
                except Exception as e:
                    print(f"[PMS] Warning: Failed to load local BiRefNet weights from {birefnet_path}: {e}")

            birefnet_model = birefnet_model.to(device)

            # Run BiRefNet
            input_images = F.resize(img_pil, (1024, 1024))
            input_tensor = F.to_tensor(input_images).unsqueeze(0).to(device)
            input_tensor = F.normalize(input_tensor, [0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            
            with torch.no_grad():
                birefnet_output = birefnet_model(input_tensor)
            
            pred = birefnet_output[-1].sigmoid().cpu().squeeze().numpy()
            refined_mask_np = np.array(Image.fromarray((pred * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BILINEAR))

            # Combine with SAM mask to ensure only the queried object is refined
            # We multiply refined_mask_np by a slightly dilated SAM mask to exclude background salient objects
            sam_mask_bool = best_sam_mask > 128
            # Simple thresholding
            final_mask_np = np.where(sam_mask_bool, refined_mask_np, 0)

            # Unload BiRefNet
            del birefnet_model
            torch.cuda.empty_cache()

            # Convert to ComfyUI outputs
            final_mask_tensor = torch.from_numpy(final_mask_np.astype(np.float32) / 255.0)
            out_masks.append(final_mask_tensor)

            # Create transparent image (RGBA)
            rgba_tensor = torch.cat([img_tensor, final_mask_tensor.unsqueeze(-1)], dim=-1)
            out_images.append(rgba_tensor)

        return (torch.stack(out_images, dim=0), torch.stack(out_masks, dim=0))
