from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FileDimensions(BaseModel):
    width: int
    height: int


class FileInfo(BaseModel):
    fileName: str
    fileType: str
    fileSize: int
    originalFileName: str
    path: str
    createdAt: int
    expiresAt: int
    dimensions: FileDimensions


class UpscaleRequest(BaseModel):
    model: str = Field(default="upscayl-standard-4x", description="Upscaling model to use")
    scale: str = Field(default="4", description="Scale factor (2, 4, or 8)")
    saveImageAs: str = Field(default="jpg", description="Output format (jpg or png)")
    enhanceFace: bool = Field(default=True, description="Enable face enhancement")
    urls: Optional[List[str]] = Field(default=None, description="Optional URLs to upscale")


class UpscaleResponse(BaseModel):
    task_id: str
    status: str
    message: str
    data: Optional[dict] = None
