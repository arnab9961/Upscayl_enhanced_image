from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import List, Optional
from app.services.upscayle_services import upscayle_service
from app.services.upscayle_schema import UpscaleRequest, UpscaleResponse


router = APIRouter(
    prefix="/upscale",
    tags=["upscale"]
)


@router.post("/images", response_model=dict)
async def upscale_images(
    files: List[UploadFile] = File(..., description="Image files to upscale (max 3)"),
    model: str = Form(default="upscayl-standard-4x", description="Upscaling model"),
    scale: str = Form(default="4", description="Scale factor (2, 4, or 8)"),
    saveImageAs: str = Form(default="jpg", description="Output format (jpg or png)"),
    enhanceFace: bool = Form(default=True, description="Enable face enhancement"),
):
    """
    Upscale one or multiple images using the Upscayl API.
    
    - **files**: Upload up to 3 image files
    - **model**: Choose the upscaling model (default: upscayl-standard-4x)
    - **scale**: Scale factor - 2x, 4x, or 8x (default: 4)
    - **saveImageAs**: Output format - jpg or png (default: jpg)
    - **enhanceFace**: Enable face enhancement (default: true)
    
    Returns task information including task_id for status checking.
    """
    # Validate file count
    if len(files) > 3:
        raise HTTPException(
            status_code=400,
            detail="Maximum 3 files allowed per request"
        )
    
    # Validate file types
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    for file in files:
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Allowed: {', '.join(allowed_types)}"
            )
    
    # Create request params
    request_params = UpscaleRequest(
        model=model,
        scale=scale,
        saveImageAs=saveImageAs,
        enhanceFace=enhanceFace
    )
    
    # Process the upscaling request
    result = upscayle_service.upscale_images(files, request_params)
    
    return result


@router.get("/task/{task_id}", response_model=dict)
async def get_task_status(task_id: str):
    """
    Get the status of an upscaling task.
    
    - **task_id**: The ID of the task to check
    
    Returns the current status and results (if completed) of the upscaling task,
    including image_urls array with the URLs of upscaled images.
    """
    result = upscayle_service.get_task_status(task_id)
    return result
