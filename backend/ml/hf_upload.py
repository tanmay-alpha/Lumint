"""
Lumint HuggingFace Hub Release & Upload Script.
Uploads trained models, model cards, and metrics JSON files to the Hugging Face Hub,
and creates the Gradio demo Space.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Ensure backend root is in sys.path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

logger = logging.getLogger("lumint.ml.hf_upload")
logging.basicConfig(level=logging.INFO)

try:
    from huggingface_hub import HfApi, create_repo
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    logger.warning("huggingface_hub is not installed. Run: pip install huggingface_hub")


def upload_model(
    model_path: str,
    repo_id: str,
    model_card_path: str,
    hf_token: str
) -> None:
    """
    Upload joblib model + model card + metrics JSON
    to HuggingFace Hub using huggingface_hub library.
    """
    if not HF_HUB_AVAILABLE:
        raise ImportError("huggingface_hub is not installed. Cannot upload model.")
        
    api = HfApi(token=hf_token)
    
    # 1. Create the repository on HF Hub if it doesn't exist
    logger.info(f"Creating/verifying repository: {repo_id}")
    create_repo(repo_id=repo_id, token=hf_token, repo_type="model", exist_ok=True)
    
    # 2. Upload the model card as README.md
    logger.info(f"Uploading model card {model_card_path} as README.md...")
    api.upload_file(
        path_or_fileobj=model_card_path,
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model"
    )
    
    # 3. Upload the model joblib file
    logger.info(f"Uploading model binary {model_path}...")
    api.upload_file(
        path_or_fileobj=model_path,
        path_in_repo=os.path.basename(model_path),
        repo_id=repo_id,
        repo_type="model"
    )
    
    # 4. Upload associated metrics JSON if it exists
    metrics_path = Path(model_path).parent / f"{Path(model_path).stem.replace('_model', '')}_metrics.json"
    if metrics_path.exists():
        logger.info(f"Uploading metrics JSON {metrics_path}...")
        api.upload_file(
            path_or_fileobj=str(metrics_path),
            path_in_repo=metrics_path.name,
            repo_id=repo_id,
            repo_type="model"
        )
    else:
        logger.warning(f"Associated metrics file not found at: {metrics_path}")
        
    logger.info(f"Successfully uploaded model artifacts to https://huggingface.co/{repo_id}")


def create_hf_demo_space(
    repo_id: str,
    hf_token: str,
    app_py_path: str = "hf_space/app.py"
) -> str:
    """
    Creates HuggingFace Spaces demo (Gradio app).
    Returns space URL.
    Demo allows anyone to upload a UPI screenshot
    and get CMFA analysis — no backend needed.
    """
    if not HF_HUB_AVAILABLE:
        raise ImportError("huggingface_hub is not installed. Cannot create Space.")
        
    api = HfApi(token=hf_token)
    
    logger.info(f"Creating/verifying Space: {repo_id}")
    # Create spaces repository
    create_repo(
        repo_id=repo_id,
        token=hf_token,
        repo_type="space",
        space_sdk="gradio",
        exist_ok=True
    )
    
    # Upload Gradio app.py
    logger.info(f"Uploading Gradio app from {app_py_path}...")
    api.upload_file(
        path_or_fileobj=app_py_path,
        path_in_repo="app.py",
        repo_id=repo_id,
        repo_type="space"
    )
    
    # Generate and upload requirements.txt for space dependencies
    requirements_content = "gradio\nnumpy\npillow\nscikit-learn\njoblib\n"
    requirements_temp = Path(app_py_path).parent / "requirements.txt"
    requirements_temp.parent.mkdir(parents=True, exist_ok=True)
    with open(requirements_temp, "w", encoding="utf-8") as f:
        f.write(requirements_content)
        
    logger.info("Uploading requirements.txt for Space...")
    api.upload_file(
        path_or_fileobj=str(requirements_temp),
        path_in_repo="requirements.txt",
        repo_id=repo_id,
        repo_type="space"
    )
    
    space_url = f"https://huggingface.co/spaces/{repo_id}"
    logger.info(f"Successfully created Space at {space_url}")
    return space_url


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Upload Lumint Models to HuggingFace Hub")
    parser.add_argument("--token", type=str, required=True, help="HF Access Token")
    parser.add_argument("--username", type=str, default="tanmay-alpha", help="HF Username")
    parser.add_argument("--upload-models", action="store_true", help="Upload trained models")
    parser.add_argument("--create-space", action="store_true", help="Create Gradio Space")
    args = parser.parse_args()
    
    models_to_upload = [
        ("upi_model.joblib", "lumint-cmfa-upi-detector", "MODEL_CARD_CMFA_GB.md"),
        ("phish_model.joblib", "lumint-phish-detector", "MODEL_CARD_PHISH_GB.md"),
        ("doc_model.joblib", "lumint-doc-detector", "MODEL_CARD_DOC_GB.md"),
        ("fusion_meta.joblib", "lumint-fusion-meta", "MODEL_CARD_FUSION_META.md")
    ]
    
    models_dir = BACKEND_ROOT / "ml" / "models"
    
    if args.upload_models:
        for model_file, repo_name, card_name in models_to_upload:
            model_path = models_dir / model_file
            card_path = models_dir / card_name
            full_repo_id = f"{args.username}/{repo_name}"
            
            if model_path.exists() and card_path.exists():
                try:
                    upload_model(
                        model_path=str(model_path),
                        repo_id=full_repo_id,
                        model_card_path=str(card_path),
                        hf_token=args.token
                    )
                except Exception as e:
                    logger.error(f"Failed to upload model {repo_name}: {e}")
            else:
                logger.warning(f"Artifact not found for {repo_name}: model_path={model_path}, card_path={card_path}")
                
    if args.create_space:
        space_repo = f"{args.username}/lumint-screenshot-forensics"
        try:
            create_hf_demo_space(
                repo_id=space_repo,
                hf_token=args.token,
                app_py_path=str(BACKEND_ROOT / "hf_space" / "app.py")
            )
        except Exception as e:
            logger.error(f"Failed to create Space: {e}")
