#!/usr/bin/env python
import json
import os

from dotenv import load_dotenv
from openai import OpenAI


class OPENROUNTER_API:
    def __init__(self, model):
        load_dotenv()

        self.base_url = os.getenv("BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.model = model

        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        self.api_extra_headers = ""

    def request(self, payload, path) -> str:
        request = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": payload}],
            response_format={"type": "json_object"},
            # reasoning_effort='low' || 'high' || 'medium'
        )

        return request.choices[0].message.content
