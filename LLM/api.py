import json
import os

from dotenv import load_dotenv
from openai import OpenAI


class OPENROUNTER_API:
    def __init__(self, context):
        load_dotenv()
        self.base_url = os.getenv("BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.model = os.getenv("MODEL")

    def ReturnJsonPattern_Interpretation(self):
        root = dict()

        root["position"]
        root["interpretation"]
        root["action_hint"]

        return root

        ### WORK IN PROGRESS
