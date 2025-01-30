from dotenv import load_dotenv
from openai import OpenAI
import os

class Request:
    client          = None

    def __init__(self):
        # Retrieve initialisation data from .env
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def prompt(self, model_instruction, user_instruction):
        completion = self.client.chat.completions.create(
            model = os.getenv("MODEL_NAME"),
            messages=[
                {
                    "role": "developer", 
                    "content": model_instruction
                },
                {
                    "role": "user",
                    "content": user_instruction
                }
            ]
        )
        return completion.choices[0].message.content

    def tts(self, text, speaker, download_path):
        response = self.client.audio.speech.create(
            model = os.getenv("TTS_MODEL_NAME"),
            voice = speaker,
            input = text
        )
        response.stream_to_file(download_path)
    
    def generate_image(self, prompt):
        response = self.client.images.generate(
            model=os.getenv("IMAGES_MODEL_NAME"),
            prompt=prompt,
            size=os.getenv("IMAGES_SIZE"),
            quality=os.getenv("IMAGES_QUALITY"),
            n=1
        )
        return response.data[0].url