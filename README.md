# AI Slop Generator

## What is this?
This project is designed to automate the generation of shortform multimedia content primarily through calls to the OpenAI API, with the following features:

- Script generation from AI models (type and format specified in /config).
- TTS audio synthesis.
- (TODO) Configurable voices assigned to speakers in scripts.

## Installation Guide:
Run the following command to install the requirements:

```bash
pip install -r requirements.txt
```

Enter your OpenAI API key into '/src/.env.format', then rename the file to '.env'.

Run the script with 
```bash
python3 src/pipeline_manager.py
```