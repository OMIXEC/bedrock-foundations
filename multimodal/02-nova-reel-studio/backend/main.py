import os
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from services.nova_reel import NovaReelService
from services.nano_banana import NanoBananaService
from services.google_veo import GoogleVeoService
import logging
import base64

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Nova Reel Marketing Studio")

# Initialize Services
# We treat services as global singletons for this demo
nova_reel = NovaReelService()
nano_banana = NanoBananaService() # Picks up GEMINI_API_KEY from env
# veo_service = GoogleVeoService(project_id=os.getenv("GCP_PROJECT_ID")) # Uncomment when ready

# Load Templates
TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "templates", "prompts.json")
try:
    with open(TEMPLATES_PATH, "r") as f:
        PROMPT_TEMPLATES = json.load(f)
except FileNotFoundError:
    logger.error("prompts.json not found!")
    PROMPT_TEMPLATES = {}

class GenerateRequest(BaseModel):
    template_id: str
    product_name: str
    params: Optional[Dict[str, Any]] = {}
    
@app.get("/templates")
def get_templates():
    return PROMPT_TEMPLATES

@app.post("/generate/video")
async def generate_video(
    template_id: str = Form(...),
    product_name: str = Form(...),
    params: str = Form("{}"),
    provider: str = Form("amazon"),
    image: Optional[UploadFile] = File(None)
):
    """
    Generates a video using Nova Reel or Veo based on template configuration.
    Currently defaults to Nova Reel for 'video' type.
    """
    template = PROMPT_TEMPLATES.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    if template["type"] != "video":
        raise HTTPException(status_code=400, detail="Template is not for video")
        
    # Parse params if string
    try:
        parsed_params = json.loads(params) if isinstance(params, str) else params
    except json.JSONDecodeError:
        parsed_params = {}

    # Interpolate Prompt
    # Merge defaults
    params_dict = parsed_params.copy()
    params_dict["product_name"] = product_name
    
    # Fill optional defaults if missing
    if "optional_params" in template:
        for k, v in template["optional_params"].items():
            if k not in params_dict:
                params_dict[k] = v
                
    prompt_text = template["template"].format(**params_dict)
    
    # TODO: If image provided, upload to S3 and pass s3Uri to Nova Reel (if supported for Image-to-Video)
    # Nova Reel supports Text-to-Video. 
    # For Image-to-Video, we might need a different call or model (e.g. Veo or Nova Reel 2.0).
    
    logger.info(f"Generating Video for: {product_name} via {provider} with prompt: {prompt_text[:50]}...")
    
    try:
        if provider == "amazon":
            result = nova_reel.generate_video(prompt_text)
            return vars(result) if hasattr(result, "__dict__") else result
        elif provider == "google":
            # Fallback to Google Veo if implemented or Image Service
            # For now, let's use nano_banana for video if it supports it, or error
            raise HTTPException(status_code=501, detail="Video generation via Google is not yet implemented in this demo.")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        error_msg = str(e)
        if "Unable to write to output location" in error_msg:
             error_msg = f"AWS Error: Bedrock cannot write to your S3 bucket. Ensure bucket '{nova_reel.output_bucket}' exists and allows 'bedrock.amazonaws.com' to PutObject. See SETUP_CLI.md."
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/generate/image")
async def generate_image(
    template_id: str = Form(...),
    product_name: str = Form(...),
    params: str = Form("{}"),
    provider: str = Form("google"),
    image: Optional[UploadFile] = File(None)
):
    """
    Generates an image using Nano Banana (Gemini/Imagen).
    """
    template = PROMPT_TEMPLATES.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    if template["type"] != "image":
        raise HTTPException(status_code=400, detail="Template is not for image")
        
    # Parse params
    try:
        parsed_params = json.loads(params) if isinstance(params, str) else params
    except json.JSONDecodeError:
        parsed_params = {}

    # Interpolate Prompt
    params_dict = parsed_params.copy()
    params_dict["product_name"] = product_name
     # Fill optional defaults
    if "optional_params" in template:
        for k, v in template["optional_params"].items():
            if k not in params_dict:
                params_dict[k] = v
                
    prompt_text = template["template"].format(**params_dict)
    
    # If Input Image is provided (e.g. for reference), we need to pass it to Gemini.
    # NanoBananaService logic would need to handle 'image' argument.
    # For now, text-to-image:
    
    try:
        if provider == "google":
            response = await nano_banana.generate_image(prompt_text, aspect_ratio=params_dict.get("aspect_ratio", "1:1"))
            # Encode images to base64 for JSON serialization
            b64_images = []
            for img in response.images:
                if hasattr(img, "image_bytes"):
                    b64_images.append(base64.b64encode(img.image_bytes).decode('utf-8'))
                elif isinstance(img, bytes):
                    b64_images.append(base64.b64encode(img).decode('utf-8'))
                else:
                    b64_images.append(str(img))

            return {
                "status": "success",
                "images": b64_images,
                "model": response.model_used
            }
        elif provider == "amazon":
            # Bedrock Nova Image generation would go here
            raise HTTPException(status_code=501, detail="Image generation via AWS Nova is not yet implemented (use Google).")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
         logger.error(f"Image Generation failed: {e}")
         raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
