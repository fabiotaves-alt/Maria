import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class GroqClient:
    def __init__(self, model="llama-3.1-70b-versatile", api_key=None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY não encontrada no .env")
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.model_name = model

    def generate(self, system_prompt, user_prompt, few_shot_examples=None, temperature=0.0, max_tokens=1000):
        start = time.time()

        messages = [{"role": "system", "content": system_prompt}]
        if few_shot_examples:
            for ex in few_shot_examples:
                messages.append({"role": "user", "content": ex["input"]})
                messages.append({"role": "assistant", "content": ex["output"]})
        messages.append({"role": "user", "content": user_prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        latency = (time.time() - start) * 1000

        return {
            "content": response.choices[0].message.content,
            "tokens_prompt": response.usage.prompt_tokens,
            "tokens_completion": response.usage.completion_tokens,
            "latency_ms": latency,
            "model": self.model_name
        }