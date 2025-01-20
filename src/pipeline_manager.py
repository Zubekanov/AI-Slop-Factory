from datetime import datetime
import json
import os
import shutil
import random
from pydub import AudioSegment
from time import sleep
from decorator_utils import *
from path_handler import *
from request_handler import *

class PipelineManager:
    pipeline_dir    = None
    pipeline_id     = None

    seed_prompt     = Request()
    script_type     = "moral_story"
    # Request handler for AI model.
    client          = None

    @process_printer("Pipeline Initialisation")
    def __init__(self):
        # Check if directory in data with pipeline_id exists.
        base_dir = PathVerifier.get_base_dir()
        # Check if the data directory exists and create it if it doesn't.
        data_dir = os.path.join(base_dir, "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # Check that the data directory contains the archive and working directories.
        archive_dir = os.path.join(data_dir, "archive")
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        working_dir = os.path.join(data_dir, "working")
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)

        if PipelineManager.working_done():
            archive_result = PipelineManager.archive_pipeline()
            if archive_result is not None:
                last_id = int(archive_result)
            else:
                # Find the highest pipeline_id in the archive directory.
                last_id = 0
                for content in os.listdir(archive_dir):
                    if int(content) > last_id:
                        last_id = int(content)
            self.pipeline_id = last_id + 1
        else:
            # Resume the working pipeline.
            self.pipeline_id = int(os.listdir(working_dir)[0])
        
        pipeline_dir = os.path.join(working_dir, str(self.pipeline_id))
        if not os.path.exists(pipeline_dir):
            os.makedirs(pipeline_dir)
        self.pipeline_dir = pipeline_dir

        # Initialise metadata file if it doesn't exist.
        metadata_file = os.path.join(pipeline_dir, "metadata.json")
        if not os.path.exists(metadata_file):
            # Fetch the seed prompt from /config/seed_prompts.data on the line that corresponds to the pipeline_id.
            # TODO: Modify seed prompt retrieval to support multiple script types.
            config_dir = os.path.join(base_dir, "config")
            seed_prompts_file = os.path.join(config_dir, "seed_prompts.data")
            with open(seed_prompts_file, "r") as file:
                seed_prompts = file.readlines()
                # Throw an error if the pipeline_id is out of bounds.
                if self.pipeline_id >= len(seed_prompts):
                    raise ValueError("Pipeline ID out of bounds.")
                self.seed_prompt = seed_prompts[self.pipeline_id]

            metadata = {
                "pipeline_id": self.pipeline_id,
                "script_type": self.script_type,
                "seed_prompt": self.seed_prompt,
                "creation_time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "done": False,
                "published":{
                    "TikTok": False,
                    "Instagram": False,
                    "Twitter": False,
                    "Facebook": False,
                }
            }
            with open(metadata_file, "w") as file:
                json.dump(metadata, file, indent=4)

    def run_pipeline(self):
        self.client = Request()
        # Check if script_raw exists in the pipeline directory, if not, generate it.
        script_raw_file = os.path.join(self.pipeline_dir, "script_raw.txt")
        if not os.path.exists(script_raw_file):
           self.generate_script_raw()
        
        # Check if script_speakers exists in the pipeline directory, if not, generate it.
        script_speakers_file = os.path.join(self.pipeline_dir, "script_speakers.json")
        if not os.path.exists(script_speakers_file):
            self.generate_script_speakers()

        # Check if the audio files directory exists in the pipeline directory, if not, create it.
        audio_files_dir = os.path.join(self.pipeline_dir, "audio_files")
        if not os.path.exists(audio_files_dir):
            os.makedirs(audio_files_dir)
            self.generate_audio_files(audio_files_dir)

        # Check if the unified audio file exists in the pipeline directory, if not, create it.
        unified_audio_file = os.path.join(self.pipeline_dir, "unified_audio.mp3")
        if not os.path.exists(unified_audio_file):
            self.unify_audio_files(audio_files_dir)
        
        # Generate accompanying images for each audio clip.
    
    @process_printer("Raw Script Generation")
    def generate_script_raw(self):
        # Fetch model instruction from /config/[script_type].prompt
        config_dir = os.path.join(PathVerifier.get_base_dir(), "config")
        prompt_file = os.path.join(config_dir, f"{self.script_type}.prompt")
        with open(prompt_file, "r") as file:
            model_instruction = file.read()
        # Get seed prompt from metadata file.
        metadata_file = os.path.join(self.pipeline_dir, "metadata.json")
        with open(metadata_file, "r") as file:
            metadata = json.load(file)
            self.seed_prompt = metadata["seed_prompt"]
        script_raw = self.client.prompt(model_instruction, self.seed_prompt)
        with open(os.path.join(self.pipeline_dir, "script_raw.txt"), "w") as file:
            file.write(script_raw)
    
    @process_printer("Script Speaker Processing")
    def generate_script_speakers(self):
        # Split script by quotes
        script_raw = open(os.path.join(self.pipeline_dir, "script_raw.txt"), "r").read()
        script_split = script_raw.split("\"")

        # Model instruction in /config/speaker_roles.prompt
        config_dir = os.path.join(PathVerifier.get_base_dir(), "config")
        prompt_file = os.path.join(config_dir, "speaker_roles.prompt")
        with open(prompt_file, "r") as file:
            model_instruction = file.read()
        
        # Request speaker roles from AI model.
        speaker_roles = self.client.prompt(model_instruction, str(script_split))
        speaker_roles = json.loads(speaker_roles)
        with open(os.path.join(self.pipeline_dir, "script_speakers.json"), "w") as file:
            json.dump(speaker_roles, file, indent=4)
    
    def generate_audio_files(self, audio_files_dir: str):
        speaker_roles = json.load(open(os.path.join(self.pipeline_dir, "script_speakers.json"), "r"))

        # Get list of speakers and assign tts voices to them.
        roles = {}
        # Get voice genders from /config/tts.json
        male_voices = []
        female_voices = []
        voice_config_path = os.path.join(PathVerifier.get_base_dir(), "config", "tts.json")
        voice_json = json.load(open(voice_config_path, "r"))
        for voice, details in voice_json.items():
            if details["gender"] == "M":
                male_voices.append(voice)
            else:
                female_voices.append(voice)

        random.shuffle(male_voices)
        random.shuffle(female_voices)

        for role in speaker_roles:
            if role["speaker"] not in roles:
                role_gender = role["gender"]
                roles[role["speaker"]] = male_voices.pop() if role_gender == "M" else female_voices.pop()
        
        # Generate audio files for each speaker.
        segment = 0
        for line in speaker_roles:
            speaker = line["speaker"]
            text = line["content"]
            # Audio file name is [segment_number - speaker].mp3
            file_path = os.path.join(audio_files_dir, f"{segment}-{speaker}.mp3")
            segment += 1
            audio_file_name = f"{segment}-{speaker}.mp3"
            self.call_tts(text, roles[speaker], file_path, audio_file_name)

    def call_tts(self, text, speaker, download_path, audio_file_name):
        @process_printer(f"{audio_file_name} TTS Request")
        def tts_request():
            self.client.tts(text, speaker, download_path)
        tts_request()
        self.client.tts(text, speaker, download_path)

    @process_printer("Audio File Concatenation")
    def unify_audio_files(self, audio_files_dir):
        # Verify that all audio files are present.
        script_speakers = json.load(open(os.path.join(self.pipeline_dir, "script_speakers.json"), "r"))
        expected_files = [f"{i}-{line['speaker']}.mp3" for i, line in enumerate(script_speakers)]
        audio_files = os.listdir(audio_files_dir)
        if set(expected_files) != set(audio_files):
            raise ValueError("Missing audio files: " + str(set(expected_files) - set(audio_files)))
        
        # Concatenate audio files, order by segment number.
        audio_files = []
        for file in expected_files:
            audio_files.append(AudioSegment.from_file(os.path.join(audio_files_dir, file), format="mp3"))
        unified_audio = AudioSegment.silent(duration=0)
        for audio in audio_files:
            unified_audio += audio
        unified_audio.export(os.path.join(self.pipeline_dir, "unified_audio.mp3"), format="mp3")


    # Check if the current working metadata file has the "done" key set to True.
    @staticmethod
    def working_done():
        data_dir = os.path.join(PathVerifier.get_base_dir(), "data")
        working_dir = os.path.join(data_dir, "working")
        working_contents = os.listdir(working_dir)
        # There should only be one directory in the working directory.
        if len(working_contents) > 1:
            raise ValueError("Multiple working directories found.")
        if len(working_contents) == 0:
            return True
        working_dir = os.path.join(working_dir, working_contents[0])
        metadata_file = os.path.join(working_dir, "metadata.json")
        with open(metadata_file, "r") as file:
            metadata = json.load(file)
            return metadata["done"]

    # Moves the working directory to the archive directory.
    # Returns the id of the pipeline that was archived.
    @staticmethod
    def archive_pipeline():
        data_dir = os.path.join(PathVerifier.get_base_dir(), "data")
        archive_dir = os.path.join(data_dir, "archive")
        working_dir = os.path.join(data_dir, "working")
        working_contents = os.listdir(working_dir)
        for content in working_contents:
            shutil.move(os.path.join(working_dir, content), archive_dir)
        if working_contents == []:
            return None
        return working_contents[0]

if __name__ == "__main__":
    test = PipelineManager()
    test.run_pipeline()