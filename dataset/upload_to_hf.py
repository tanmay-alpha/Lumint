import os
import json
from PIL import Image

try:
    from datasets import Dataset, DatasetDict, Features, Image as HFImage, Value, ClassLabel
    from huggingface_hub import HfApi
    HAS_HF = True
except ImportError:
    HAS_HF = False

def prepare_hf_dataset() -> DatasetDict:
    """
    Loads local JSONL and PNG images to build a HuggingFace DatasetDict.
    """
    if not HAS_HF:
        raise ImportError("HuggingFace 'datasets' library is not installed.")
        
    splits = ["train", "val", "test"]
    data_by_split = {s: [] for s in splits}
    
    with open("dataset/metadata.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                split = item["split"]
                
                # Load PIL image
                img_path = item["image_path"]
                if os.path.exists(img_path):
                    # We store image as path or PIL Image object
                    item["image"] = Image.open(img_path)
                else:
                    item["image"] = None
                    
                # Unpack features dictionary for flat fields in HF
                for k, v in item["features"].items():
                    item[f"feature_{k}"] = v
                    
                # Clean up nested features dict to avoid Schema mismatch
                del item["features"]
                data_by_split[split].append(item)
                
    # Define Hugging Face dataset features schema
    hf_features = Features({
        "id": Value("string"),
        "split": Value("string"),
        "label": ClassLabel(names=["genuine", "forged"]),
        "app": Value("string"),
        "forgery_type": Value("string"),
        "utr": Value("string"),
        "amount": Value("string"),
        "image_path": Value("string"),
        "image": HFImage(),
        "generation_method": Value("string"),
        "difficulty": Value("string"),
        "feature_brand_palette_distance": Value("float32"),
        "feature_text_height_variance": Value("float32"),
        "feature_ela_hotspot_density": Value("float32"),
        "feature_utr_valid": Value("bool"),
        "feature_ocr_confidence": Value("float32"),
        "feature_font_consistent": Value("bool")
    })
    
    dataset_dict = {}
    for split in splits:
        # Re-format list of dicts to dict of lists for HF Dataset construction
        keys = list(hf_features.keys())
        dict_data = {k: [] for k in keys}
        for item in data_by_split[split]:
            for k in keys:
                # Fallback for nulls or missing keys
                val = item.get(k, None)
                # Map none for string values
                if val is None and k == "forgery_type":
                    val = "none"
                dict_data[k].append(val)
                
        dataset_dict[split] = Dataset.from_dict(dict_data, features=hf_features)
        
    return DatasetDict(dataset_dict)

def upload_dataset(token: str) -> None:
    """
    Pushes the DatasetDict to the Hugging Face hub.
    """
    if not token or token == "your_huggingface_write_token_here":
        print("Skipping HuggingFace upload: HF_TOKEN is empty or placeholder.")
        return
        
    print("Preparing HuggingFace dataset split formats...")
    dataset_dict = prepare_hf_dataset()
    
    repo_id = "tanmay-alpha/upi-fraudbench-2026"
    print(f"Uploading dataset to Hugging Face Hub at '{repo_id}'...")
    
    try:
        dataset_dict.push_to_hub(repo_id, token=token)
        print("Dataset successfully pushed to HuggingFace Hub!")
    except Exception as e:
        print(f"Error uploading dataset to HuggingFace Hub: {e}")

def main():
    token = os.getenv("HF_TOKEN", "your_huggingface_write_token_here")
    if HAS_HF:
        upload_dataset(token)
    else:
        print("HuggingFace dependencies are not loaded. Cannot run upload.")

if __name__ == "__main__":
    main()
