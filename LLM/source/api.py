#!/usr/bin/env python
import base64
import json
import os

from dotenv import load_dotenv
from openai import OpenAI


class OPENROUNTER_API:
    def __init__(self, model):
        load_dotenv()

        self.base_url = os.getenv("BASE_URL")
        self.api_key = os.getenv("API_KEY_GUERRA")
        self.model = model

        if not self.base_url or not self.api_key:
            raise OSError("BASE_URL e API_KEY devem estar definidos no .env")
        if not self.model:
            raise ValueError("O 'model' deve ser especificado.")

        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        return f"data:image/jpg;base64,{base64_image}"

    def message_image(self, text_prompt, image_data_url):
        msg = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text_prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }
        ]

        return msg

    def message(self, text_prompt):
        msg = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text_prompt},
                ],
            }
        ]

        return msg

    def request(self, text_prompt: str, image_path: str) -> str:
        if image_path is not None:
            image_data_url = self._encode_image(image_path)

        # try:
        if True:
            if image_path is not None:
                messages = self.message_image(text_prompt, image_data_url)
            else:
                messages = self.message(text_prompt)

            request = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=3000,
                response_format={"type": "json_object"},
            )

            usage = request.usage
            print(f"--- Relatório de Tokens ---")
            print(f"Entrada (Prompt + Imagem): {usage.prompt_tokens}")
            print(f"Saída (Resposta do Modelo): {usage.completion_tokens}")
            print(f"Total: {usage.total_tokens}")
            print(f"---------------------------")

            return json.loads(request.choices[0].message.content)

        # except FileNotFoundError:
        #    return f"Erro: Arquivo de imagem não encontrado em {image_path}"
        # except Exception as e:
        #    return f"Ocorreu um erro: {e}"
