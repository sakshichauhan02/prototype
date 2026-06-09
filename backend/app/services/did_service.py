import httpx
import asyncio
import base64
from typing import Dict, Any, Optional
from app.config import settings
from app.services.emotion_service import emotion_service

class DIDService:
    @staticmethod
    async def generate_avatar_video(text: str) -> str:
        """
        Generates a talking avatar video speaking the provided text using the D-ID Talks API.
        Automatically maps the text language to appropriate Microsoft Neural voices:
        - Hindi -> hi-IN-SwaraNeural
        - Hinglish -> en-IN-NeerjaNeural
        - English -> en-US-JennyNeural
        """
        api_key = getattr(settings, "DID_API_KEY", "")
        
        # fallback mock video in case key is not set or invalid
        mock_video = "https://www.w3schools.com/html/mov_bbb.mp4"
        
        if not api_key or api_key.strip() == "":
            print("Warning: DID_API_KEY is not configured. Returning mock avatar video.")
            return mock_video

        # Determine voice based on text language
        lang = emotion_service._detect_language_local(text)
        if lang == "Hindi":
            voice_id = "hi-IN-SwaraNeural"
        elif lang == "Hinglish":
            voice_id = "en-IN-NeerjaNeural"
        else:
            voice_id = "en-US-JennyNeural"

        # Prepare Basic Auth header
        # D-ID API keys require base64(api_key + ":")
        auth_str = f"{api_key}:"
        auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        payload = {
            "source_url": "https://clips-presenters.d-id.com/v2/lana/TtreMLgSnL/b4HH6GpEhF/image.png",
            "script": {
                "type": "text",
                "subtitles": "false",
                "provider": {
                    "type": "microsoft",
                    "voice_id": voice_id
                },
                "input": text
            },
            "config": {
                "fluent": "false",
                "pad_audio": "0.0"
            }
        }
        
        create_url = "https://api.d-id.com/talks"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                print(f"Creating D-ID Talk with voice {voice_id} for text: '{text[:30]}...'")
                response = await client.post(create_url, json=payload, headers=headers)
                
                if response.status_code == 201 or response.status_code == 200:
                    data = response.json()
                    talk_id = data.get("id")
                    if not talk_id:
                        print(f"Warning: D-ID response missing talk ID: {data}")
                        return mock_video
                    
                    # Begin polling for completion
                    poll_url = f"https://api.d-id.com/talks/{talk_id}"
                    max_polls = 120
                    poll_interval = 3.0
                    
                    print(f"D-ID Talk created successfully with ID: {talk_id}. Polling for video...")
                    
                    for poll_num in range(max_polls):
                        await asyncio.sleep(poll_interval)
                        poll_resp = await client.get(poll_url, headers=headers)
                        
                        if poll_resp.status_code == 200:
                            poll_data = poll_resp.json()
                            status = poll_data.get("status")
                            print(f"Poll #{poll_num + 1} status: {status}")
                            
                            if status == "done":
                                result_url = poll_data.get("result_url")
                                if result_url:
                                    print(f"Success! D-ID video ready at: {result_url}")
                                    return result_url
                            elif status == "failed":
                                print(f"Warning: D-ID video generation failed for talk ID: {talk_id}")
                                return mock_video
                        else:
                            print(f"Warning: D-ID poll request returned status {poll_resp.status_code}")
                            
                    print("Warning: D-ID video polling timed out. Returning mock video.")
                    return mock_video
                else:
                    print(f"Warning: D-ID API returned status {response.status_code}: {response.text[:200]}")
                    return mock_video
                    
        except Exception as e:
            print(f"Warning: Exception encountered during D-ID video generation: {e}")
            return mock_video

did_service = DIDService()
