#!/usr/bin/env python
import json

from openai import OpenAI


class LLMApi:
    def __init__(self, base_url, model, key_path="key.json"):
        with open(key_path) as key_file:
            self.key = json.load(key_file)["key"]
        self.client = OpenAI(base_url=base_url, api_key=self.key)
        self.model = model

    def setInitialContext(self, context: str):
        self.context = context

    def getReturnJsonPattern(self) -> dict:
        root = dict()
        root["action"] = "this is your action, can be move or rotate"
        root["obj_moved_id"] = "this is the id of the object you want to move"
        root["pos"] = (
            "can be a x;y delta offset in case of action = move or a value between [0,90,180,270] in case of rotation"
        )
        root["thoughts"] = "this is your thoughts"
        return root

    def generate(self, msg: dict):
        self.payload = "<context>\n"
        self.payload += self.context
        self.payload += "\nFollow the bellow json to answer:\n"
        self.payload += json.dumps(self.getReturnJsonPattern())
        self.payload += "\n</context>\n"
        self.payload += "<current_turn>\n"
        self.payload += json.dumps(msg)
        self.payload += "\n</current_turn>\n"

    def request(self) -> str:
        request = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": self.payload}],
            response_format="json_object",
        )
        return request.choices[0].message.content


def main():
    api = LLMApi("https://openrouter.ai/api/v1", model="deepseek/deepseek-v3-base:free")

    api.setInitialContext(
        "You are observing a simulation with several moving agents and a door. You can press one of six buttons: btn1, btn2, btn3, btn4, btn5, btn6. Your goal is to help all agents exit through the door. Use the outcomes of each action to understand the system and act accordingly. After each step, think out loud and choose the next button."
    )

    data = {}
    api.generate(msg=data)

    print(api.request())


if __name__ == "__main__":
    main()
