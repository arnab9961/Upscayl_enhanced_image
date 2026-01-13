import requests
import json
import time
import asyncio
import logging
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.services.upscayle_schema import UpscaleRequest, UpscaleResponse

logger = logging.getLogger(__name__)


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
    
    async def upscale_images_sync(
        self,
        files: List[UploadFile],
        request_params: UpscaleRequest,
        max_wait_time: int = 1200,  # 20 minutes max
    ) -> dict:
        """
        Upscale images synchronously - waits for processing to complete
        
        Args:
            files: List of image files to upscale
            request_params: Upscaling parameters
            max_wait_time: Maximum time to wait in seconds (default: 1200)
            
        Returns:
            dict: Completed task with download URLs
        """
        # Start the upscaling task
        logger.info("Starting upscaling task...")
        task_response = self.upscale_images(files, request_params)
        
        if "data" not in task_response or "taskId" not in task_response["data"]:
            raise HTTPException(
                status_code=500,
                detail="Failed to create upscaling task"
            )
        
        task_id = task_response["data"]["taskId"]
        logger.info(f"Task created with ID: {task_id}")
        start_time = time.time()
        
        # Fast polling for quick tasks: check frequently at first
        poll_intervals = [0.5, 0.5, 1, 1, 2, 2, 3, 5, 10]  # seconds
        poll_index = 0
        check_count = 0
        
        # Poll for task completion
        while True:
            # Get task status immediately (no delay on first check)
            try:
                status_response = self.get_task_status(task_id)
                check_count += 1
                elapsed_time = time.time() - start_time
                
                # Log the full response for debugging
                logger.info(f"Check #{check_count} - Task {task_id} response: {json.dumps(status_response)}")
                
                if "data" in status_response:
                    data = status_response["data"]
                    task_status = data.get("status", "").upper()  # Normalize to uppercase
                    
                    # Check for completion - PROCESSED means downloadable links are ready
                    if task_status in ["PROCESSED", "COMPLETED", "COMPLETE", "SUCCESS", "DONE"]:
                        logger.info(f"Task {task_id} completed successfully after {elapsed_time:.1f} seconds")
                        return status_response
                    
                    # Check if task failed
                    if task_status in ["FAILED", "ERROR"]:
                        error_msg = data.get("error", "Unknown error")
                        logger.error(f"Task {task_id} failed: {error_msg}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Image upscaling failed: {error_msg}"
                        )
                    
                    # Task is still processing (ENHANCING, PENDING, etc.)
                    if task_status in ["ENHANCING", "PENDING", "PROCESSING", "QUEUED"]:
                        logger.info(f"Task {task_id} status: {task_status} (elapsed: {elapsed_time:.1f}s)")
                    else:
                        # Unknown status - log and continue polling
                        logger.warning(f"Task {task_id} unknown status: {task_status} (elapsed: {elapsed_time:.1f}s)")
                else:
                    logger.warning(f"Unexpected response format for task {task_id}: {status_response}")
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking task status: {str(e)}")
            
            # Check timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                logger.error(f"Task {task_id} timeout after {elapsed_time:.1f} seconds")
                raise HTTPException(
                    status_code=408,
                    detail=f"Task processing timeout after {int(elapsed_time)} seconds. Task ID: {task_id}. Check status at /upscale/task/{task_id}"
                )
            
            # Determine next poll interval (progressive backoff)
            current_interval = poll_intervals[min(poll_index, len(poll_intervals) - 1)]
            poll_index += 1
            
            # Wait before next poll (non-blocking)
            await asyncio.sleep(current_interval)


# Create a singleton instance
upscayle_service = UpscayleService()
