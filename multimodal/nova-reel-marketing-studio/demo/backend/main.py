import os
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from services.nova_reel import NovaReelService
from services.nano_banana import NanoBananaService
from services.google_veo import GoogleVeoService
import logging

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
    request: GenerateRequest,
    image: Optional[UploadFile] = File(None)
):
    """
    Generates a video using Nova Reel or Veo based on template configuration.
    Currently defaults to Nova Reel for 'video' type.
    """
    template = PROMPT_TEMPLATES.get(request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    if template["type"] != "video":
        raise HTTPException(status_code=400, detail="Template is not for video")
        
    # Interpolate Prompt
    # Merge defaults
    params = request.params.copy()
    params["product_name"] = request.product_name
    
    # Fill optional defaults if missing
    if "optional_params" in template:
        for k, v in template["optional_params"].items():
            if k not in params:
                params[k] = v
                
    prompt_text = template["template"].format(**params)
    
    # TODO: If image provided, upload to S3 and pass s3Uri to Nova Reel (if supported for Image-to-Video)
    # Nova Reel supports Text-to-Video. 
    # For Image-to-Video, we might need a different call or model (e.g. Veo or Nova Reel 2.0).
    
    logger.info(f"Generating Video for: {request.product_name} with prompt: {prompt_text[:50]}...")
    
    try:
        # Call Nova Reel
        # For demo, result is a job ID/ARN.
        result = nova_reel.generate_video(prompt_text)
        return vars(result) if hasattr(result, "__dict__") else result
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/image")
async def generate_image(
    request: GenerateRequest,
    image: Optional[UploadFile] = File(None)
):
    """
    Generates an image using Nano Banana (Gemini/Imagen).
    """
    template = PROMPT_TEMPLATES.get(request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    if template["type"] != "image":
        raise HTTPException(status_code=400, detail="Template is not for image")
        
    # Interpolate Prompt
    params = request.params.copy()
    params["product_name"] = request.product_name
     # Fill optional defaults
    if "optional_params" in template:
        for k, v in template["optional_params"].items():
            if k not in params:
                params[k] = v
                
    prompt_text = template["template"].format(**params)
    
    # If Input Image is provided (e.g. for reference), we need to pass it to Gemini.
    # NanoBananaService logic would need to handle 'image' argument.
    # For now, text-to-image:
    
    try:
        response = await nano_banana.generate_image(prompt_text, aspect_ratio=params.get("aspect_ratio", "1:1"))
        return {
            "status": "success",
            "images": response.images, # In real app, convert bytes to URL/Base64
            "model": response.model_used
        }
    except Exception as e:
         logger.error(f"Image Generation failed: {e}")
         raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
