# ai_services/gemini_service.py

import os
import json
import time
import tempfile
from typing import List, Tuple
from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from .taxonomy import get_ai_taxonomy
from .prompts import get_incident_analysis_prompt
from config import get_settings

settings = get_settings()

def get_gemini_client():
    return genai.Client(api_key=settings.google_api_key)

def analyze_media(media_data: List[Tuple[bytes, str]], db: Session, user_context: str = "") -> dict:
    """
    Analyzes multiple media files (image, video, or audio) using Gemini AI.
    Grounds the AI's suggestions in the current DB taxonomy and optional user text.
    """
    client = get_gemini_client()
    taxonomy = get_ai_taxonomy(db)
    prompt = get_incident_analysis_prompt(taxonomy, user_context)
    
    parts = []
    temp_files_on_disk = []
    gemini_files_to_delete = []
    
    try:
        # 1. Process each media file into Gemini parts
        for file_bytes, content_type in media_data:
            content_type_lower = content_type.lower()
            is_image = "image" in content_type_lower
            is_video = "video" in content_type_lower
            is_audio = "audio" in content_type_lower
            
            if is_image:
                # Images can be sent as direct base64 parts
                parts.append(types.Part.from_bytes(data=file_bytes, mime_type=content_type))
            elif is_video or is_audio:
                # Video/Audio requires the Gemini File API
                suffix = ".mp4" if is_video else ".mp3"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name
                    temp_files_on_disk.append(tmp_path)
                
                # Upload to Gemini infrastructure
                file_metadata = client.files.upload(path=tmp_path)
                
                # Poll for processing completion
                while file_metadata.state.name == "PROCESSING":
                    time.sleep(2)
                    file_metadata = client.files.get(name=file_metadata.name)
                
                if file_metadata.state.name == "FAILED":
                    continue # Skip this file but try the others
                
                parts.append(file_metadata)
                gemini_files_to_delete.append(file_metadata.name)

        if not parts:
            raise Exception("No valid media files were successfully processed.")

        # 2. Generate content with ALL parts + the grounding prompt
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=parts + [prompt],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                temperature=0,
            ),
        )
        
        # 3. Parse and clean the JSON response
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_text)
        
        # Post-process: Ensure multi-select fields are lists
        for field in ["incident_type", "incident_group", "sub_group"]:
            if field in data and isinstance(data[field], str):
                data[field] = [data[field]]
        
        return data

    except Exception as e:
        print(f"ERROR in analyze_media: {str(e)}")
        return {"error": str(e), "message": "Failed to analyze media with AI."}
        
    finally:
        # Cleanup: Remove files from Gemini cloud
        for name in gemini_files_to_delete:
            try: client.files.delete(name=name)
            except: pass
        # Cleanup: Remove temporary files from local disk
        for path in temp_files_on_disk:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except: pass
