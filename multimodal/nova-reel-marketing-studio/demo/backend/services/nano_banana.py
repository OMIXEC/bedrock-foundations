import os
import logging
import asyncio
from typing import Optional, List, Dict, Any, Union
# Re-using the logic from the mcp directory if possible, but for simplicity/robustness in this demo, 
# we will implement a direct client here that mimics the behavior (Auto-selection of Flash/Pro) using google-genai
import google.genai
from google.genai import types
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ImageGenerationResponse(BaseModel):
    images: List[Any] # URL or PIL Image depending on implementation
    model_used: str

class NanoBananaService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            # Try vertex AI if no API Key
            self.client = google.genai.Client(vertexai=True, project=os.getenv("GCP_PROJECT_ID"), location=os.getenv("GCP_REGION", "us-central1"))
        else:
            self.client = google.genai.Client(api_key=self.api_key)

    async def generate_image(
        self, 
        prompt: str, 
        number_of_images: int = 1, 
        aspect_ratio: str = "1:1",
        model_tier: str = "auto"
    ) -> ImageGenerationResponse:
        """
        Generates images using Gemini models with smart selection.
        """
        model = self._select_model(prompt, model_tier, number_of_images)
        logger.info(f"Generating image with model: {model} for prompt: {prompt[:50]}...")
        
        try:
            response = self.client.models.generate_images(
                model=model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=number_of_images,
                    aspect_ratio=aspect_ratio,
                    # Add safety settings if needed
                )
            )
            
            # Helper to save or return images. For now we assume the client returns objects we can process.
            # In a real app we might upload to GCS/S3 here.
            
            return ImageGenerationResponse(
                images=response.generated_images,
                model_used=model
            )

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise

    def _select_model(self, prompt: str, tier: str, count: int) -> str:
        """
        Selects between Gemini 3 Pro (imagen-3.0-generate-002 likely) and Flash based on heuristics.
        """
        if tier == "pro":
            return "imagen-3.0-generate-001" # Or specific Pro model name
        if tier == "flash":
            return "imagen-3.0-fast-generate-001" # Or specific Flash name
            
        # Auto logic
        quality_keywords = ["4k", "professional", "high-res", "hyper-realistic", "detailed"]
        if any(k in prompt.lower() for k in quality_keywords):
            return "imagen-3.0-generate-001"
        
        if count > 2:
            return "imagen-3.0-fast-generate-001"
            
        return "imagen-3.0-generate-001" # Default to quality
