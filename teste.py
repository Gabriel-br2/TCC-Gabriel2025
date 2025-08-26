import ollama

res = ollama.chat(
    model="llava",
    messages=[
        {"role": "user", "content": "Describe this image:", "images": ["./teste.jpg"]}
    ],
)

image_interpretation = res["message"]["content"]

res = ollama.chat(
    model="qwen3",
    messages=[
        {
            "role": "user",
            "content": f"based on the interpretation of this image created by another AI agent, develop an action plan: {image_interpretation}",
        }
    ],
)

print(res["message"]["content"])
