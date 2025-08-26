import json
import re

import ollama


def obtain_image_description(path):
    prompt = """
    Analyze the provided image and generate a JSON with the following fields:
    - position: coordinates or bounding box of the relevant object in the image (x, y, width, height)
    - interpretation: textual description of what you see in the image
    - action_hint: an indication of how to achieve a specific goal related to the object in the image

    The JSON should have this exact structure:
    {
    "position": "string",
    "interpretation": "string",
    "action_hint": "string"
    }
    return only the JSON, without further explanation.
    """

    res = ollama.chat(
        model="llava",
        messages=[{"role": "user", "content": f"{prompt}", "images": [f"./{path}"]}],
    )

    asw = res["message"]["content"]
    asw = asw.replace("```json", "")
    asw = asw.replace("```", "")

    print("llava:", asw)
    return json.loads(asw)


def get_command_movement(image_interpretation):
    prompt = """
    Generates concrete actions based on the JSON.

    Example output:
    in case of a movement action: {'action': 'move', 'object_id': 0, 'dx': 10, 'dy': -5},
    in case of a rotation action: {'action': 'rotate', 'object_id': 0}

    respond only with this json and nothing else

    Input:
    """

    res = ollama.chat(
        model="qwen3",
        messages=[
            {
                "role": "user",
                "content": f"{prompt} {image_interpretation}",
            }
        ],
    )

    asw = res["message"]["content"]
    asw = asw.replace("```json", "")
    asw = asw.replace("```", "")
    cleaned = re.sub(r"<think>.*?</think>", "", asw, flags=re.DOTALL)

    print("qwen:", cleaned.strip())
    return json.loads(cleaned.strip())
