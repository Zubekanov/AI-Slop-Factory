from dotenv import load_dotenv
from openai import OpenAI
import os

class Request:
    OPENAI_API_KEY  = None
    MODEL_NAME      = None
    TTS_MODEL_NAME  = None

    client          = None

    def __init__(self):
        # Retrieve initialisation data from .env
        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.MODEL_NAME = os.getenv("MODEL_NAME")
        self.TTS_MODEL_NAME = os.getenv("TTS_MODEL_NAME")

        self.client = OpenAI(api_key=self.OPENAI_API_KEY)

    def prompt(self, model_instruction, user_instruction):
        completion = self.client.chat.completions.create(
            model = self.MODEL_NAME,
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
        print(f"Model Name: {self.MODEL_NAME}")
        return completion.choices[0].message.content

    def tts(self, text, speaker, download_path):
        response = self.client.audio.speech.create(
            model = self.TTS_MODEL_NAME,
            voice = speaker,
            input = text
        )
        response.stream_to_file(download_path)