import os

class ArizeConfig:
    def __init__(self):
        self.api_key = os.getenv("ARIZE_API_KEY")
        self.api_url = os.getenv("ARIZE_API_URL")