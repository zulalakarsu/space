from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import numpy as np
import cv2
import base64
from typing import Optional
import io
from PIL import Image
import uvicorn
import os
import requests
import json
from openai import OpenAI


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="Image and Text Processing API")

# Pydantic models for request validation
class NavigateRequest(BaseModel):
    text: str

class IdentifyImageRequest(BaseModel):
    entity_name: str
    image: Optional[str] = None  # Base64 encoded image

# Helper function to decode base64 images
def decode_image(base64_string):
    try:
        # Remove potential data URL prefix
        if 'base64,' in base64_string:
            base64_string = base64_string.split('base64,')[1]
            
        # Decode base64 string to bytes
        img_data = base64.b64decode(base64_string)
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(img_data, np.uint8)
        
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")

# Helper function for image identification logic
def identify_entity_in_image(image, entity_name):
    """
    Identify if the specified entity is present in the image using OpenAI's API.
    """
    # Convert OpenCV image to base64 for API request
    if isinstance(image, np.ndarray):
        # Convert from BGR to RGB (OpenCV uses BGR by default)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
    else:
        image_pil = image
    
    # Convert image to base64
    buffer = io.BytesIO()
    image_pil.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # Prepare the API request to OpenAI
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    # Using GPT-4 Vision API for identification
    payload = {
        "model": "gpt-4o",  # or the latest vision model
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Is there a {entity_name} in this image? Please respond with only 'true' or 'false'."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 10  # Keep response concise
    }

    
    try:
        response = openai_client.completions.create(**payload)
        # response = requests.post(
        #     "https://api.openai.com/v1/chat/completions",
        #     headers=headers,
        #     json=payload
        # )
        
        # Check if the request was successful
        # response.raise_for_status()
        
        # Parse the response
        # result = response.json()
        response_text = response.choices[0].message.content
        
        # Determine if the entity was found based on the response
        if "true" in response_text:
            return True
        elif "false" in response_text:
            return False
        else:
            # If response is unclear, default to False
            return False
            
    except Exception as e:
        # Log the error (in a production environment)
        print(f"Error in OpenAI API call: {str(e)}")
        # Default to False on error
        return False

# Helper function for image description
def generate_description(image):
    """
    Generate a detailed description of the image content using OpenAI's API.
    """
    # Convert OpenCV image to base64 for API request
    if isinstance(image, np.ndarray):
        # Convert from BGR to RGB (OpenCV uses BGR by default)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
    else:
        image_pil = image
    
    # Convert image to base64
    buffer = io.BytesIO()
    image_pil.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # Prepare the API request to OpenAI
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    # Using GPT-4 Vision API for image description
    payload = {
        "model": "gpt-4o",  # or the latest vision model
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in detail. Include information about objects, people, activities, setting, colors, and any notable elements."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4096  # Adjust based on desired description length
    }
    
    try:
        response = openai_client.completions.create(**payload)
        description = response.choices[0].message.content
        return description
            
    except Exception as e:
        # Log the error (in a production environment)
        print(f"Error in OpenAI API call: {str(e)}")
        
        # Fallback to basic description on error
        width, height = image_pil.size
        return f"Error generating AI description. Basic info: {width}x{height} image."

# Endpoint 1: Identify image
@app.post("/identify", response_class=JSONResponse)
async def identify_image(entity_name: str = Form(...), image: UploadFile = File(...)):
    """
    Identify if a specific entity exists in an image.
    
    Parameters:
    - entity_name (str): The name of the entity to search for
    - image (File): The uploaded image file
    
    Returns:
    - JSON with identification result (True/False)
    """
    try:
        # Read image file
        content = await image.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Perform entity identification
        result = identify_entity_in_image(img, entity_name)
        
        return {"found": result, "entity": entity_name}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 1 Alternative: Identify image with base64
@app.post("/identify_base64")
async def identify_image_base64(request: IdentifyImageRequest):
    """
    Identify if a specific entity exists in a base64-encoded image.
    
    Parameters:
    - request (IdentifyImageRequest): Contains entity_name and base64-encoded image
    
    Returns:
    - JSON with identification result (True/False)
    """
    try:
        if not request.image:
            raise HTTPException(status_code=400, detail="Image data is required")
        
        # Decode base64 image
        img = decode_image(request.image)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Perform entity identification
        result = identify_entity_in_image(img, request.entity_name)
        
        return {"found": result, "entity": request.entity_name}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 2: Navigate
@app.post("/navigate", response_class=JSONResponse)
async def navigate(request: NavigateRequest):
    """
    Process text input and respond with navigation instructions.
    
    Parameters:
    - request (NavigateRequest): Contains text input for navigation
    
    Returns:
    - JSON with navigation response
    """
    try:
        # This would typically connect to a navigation service or NLP model
        # For demonstration, we'll return a simple response based on keywords
        
        input_text = request.text.lower()
        
        # Simplified keyword-based response generation
        if "left" in input_text:
            response = "Navigating to the left"
        elif "right" in input_text:
            response = "Navigating to the right"
        elif "forward" in input_text or "ahead" in input_text:
            response = "Moving forward"
        elif "back" in input_text or "behind" in input_text:
            response = "Moving backward"
        elif "stop" in input_text:
            response = "Stopping navigation"
        else:
            response = "I didn't understand the navigation command. Please try again with directions like 'left', 'right', 'forward', 'back', or 'stop'."
        
        return {"response": response, "original_text": request.text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 3: Describe
@app.post("/describe", response_class=JSONResponse)
async def describe_image(image: UploadFile = File(...)):
    """
    Generate a description of an uploaded image.
    
    Parameters:
    - image (File): The uploaded image file
    
    Returns:
    - JSON with image description
    """
    try:
        # Read image file
        content = await image.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Generate image description
        description = generate_description(img)
        
        return {"description": description}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 3 Alternative: Describe with base64
@app.post("/describe_base64", response_class=JSONResponse)
async def describe_image_base64(image_data: dict):
    """
    Generate a description of a base64-encoded image.
    
    Parameters:
    - image_data (dict): Contains base64-encoded image in 'image' field
    
    Returns:
    - JSON with image description
    """
    try:
        if 'image' not in image_data:
            raise HTTPException(status_code=400, detail="Image data is required")
        
        # Decode base64 image
        img = decode_image(image_data['image'])
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Generate image description
        description = generate_description(img)
        
        return {"description": description}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint for API information
@app.get("/", response_class=JSONResponse)
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "api": "Image and Text Processing API",
        "version": "1.0",
        "endpoints": [
            {"path": "/identify", "method": "POST", "description": "Identify entities in images"},
            {"path": "/identify_base64", "method": "POST", "description": "Identify entities in base64-encoded images"},
            {"path": "/navigate", "method": "POST", "description": "Process navigation text commands"},
            {"path": "/describe", "method": "POST", "description": "Generate descriptions for images"},
            {"path": "/describe_base64", "method": "POST", "description": "Generate descriptions for base64-encoded images"}
        ]
    }

# if __name__ == "__main__":
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)