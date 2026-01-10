import requests
import json
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.services.upscayle_schema import UpscaleRequest, UpscaleResponse


class UpscayleService:
    def __init__(self):
        self.api_url = settings.UPSCAYLE_API_URL or "https://api.upscayl.org"
        self.api_key = settings.UPSCAYLE_API_KEY
        
        if not self.api_key:
            raise ValueError("UPSCAYLE_API_KEY not set in environment variables")
    
    def upscale_images(
        self,
        files: List[UploadFile],
        request_params: UpscaleRequest
    ) -> dict:
        """
        Upscale one or multiple images using the Upscayl API
        
        Args:
            files: List of image files to upscale
            request_params: Upscaling parameters
            
        Returns:
            dict: API response with task information
        """
        try:
            # Prepare the files for upload
            files_data = {}
            for idx, file in enumerate(files):
                file_content = file.file.read()
                files_data[f"{idx}.file"] = (file.filename, file_content, file.content_type)
                file.file.seek(0)  # Reset file pointer
            
            # Prepare the payload
            payload = {
                "model": request_params.model,
                "scale": request_params.scale,
                "saveImageAs": request_params.saveImageAs,
                "enhanceFace": str(request_params.enhanceFace).lower(),
            }
            
            # Add URLs if provided
            if request_params.urls:
                payload["urls"] = json.dumps(request_params.urls)
            
            # Prepare headers
            headers = {
                "X-API-Key": self.api_key
            }
            
            # Make the API request
            url = f"{self.api_url}/start-task"
            response = requests.post(
                url,
                data=payload,
                files=files_data,
                headers=headers,
                timeout=30
            )
            
            # Check for errors
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error communicating with Upscayl API: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing upscale request: {str(e)}"
            )
    
    def get_task_status(self, task_id: str) -> dict:
        """
        Get the status of an upscaling task
        
        Args:
            task_id: The task ID to check
            
        Returns:
            dict: Task status information with image URLs
        """
        try:
            url = f"{self.api_url}/get-task-status"
            payload = {"data": {"taskId": task_id}}
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract image URLs from the response
            if "data" in result:
                data = result["data"]
                image_urls = []
                task_status = data.get("status", "")
                
                # Check if files exist in the response
                if "files" in data and isinstance(data["files"], list):
                    base_url = "https://upscayl.org"  # Base CDN URL
                    for file_info in data["files"]:
                        if isinstance(file_info, dict):
                            # Check for direct URL first
                            if "url" in file_info:
                                image_urls.append(file_info["url"])
                            # Otherwise construct from path
                            elif "path" in file_info:
                                image_url = f"{base_url}/{file_info['path']}"
                                image_urls.append(image_url)
                
                result["image_urls"] = image_urls
                result["task_status"] = task_status
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching task status: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing task status: {str(e)}"
            )


# Create a singleton instance
upscayle_service = UpscayleService()
