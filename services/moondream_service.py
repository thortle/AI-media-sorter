#!/usr/bin/env python3
"""
Simple HTTP service wrapping Moondream2 for photo uploads.
Run this on the host machine - Docker will call it for AI descriptions.

Usage: python services/moondream_service.py
"""

import sys
from pathlib import Path

# Add scripts path for existing vision model
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts/generate"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Moondream Service")

# Lazy load model (only when first request comes in)
vision_model = None


def get_model():
    global vision_model
    if vision_model is None:
        print("Loading Moondream2 model...")
        from models.vision_model import MoondreamVisionModel
        vision_model = MoondreamVisionModel()
        print("Model ready!")
    return vision_model


class DescribeRequest(BaseModel):
    photo_path: str


@app.post("/describe")
async def describe_image(request: DescribeRequest):
    """Generate description for an image."""
    path = Path(request.photo_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    model = get_model()
    description = model.analyze_image(str(path))

    if not description:
        raise HTTPException(status_code=500, detail="Failed to generate description")

    return {"description": description}


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": vision_model is not None}


if __name__ == "__main__":
    print("Starting Moondream service on port 8001...")
    print("Docker will call this for AI descriptions during uploads.")
    uvicorn.run(app, host="0.0.0.0", port=8001)
