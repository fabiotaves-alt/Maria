"""Cliente para LLMs com suporte a múltiplos providers."""
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass

from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env (Lia/.env ou raiz)
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(_ENV_PATH)
load_dotenv()  # fallback para .env na raiz


def load_few_shot_examples(path: str) -> List[Dict[str, str]]:
    """
    Carrega exemplos few-shot de um arquivo JSON.
    
    O arquivo deve conter uma lista de objetos com chaves "input" e "output".
    
    Args:
        path: Caminho para o arquivo JSON
        
    Returns:
        Lista de dicionários {"input": ..., "output": ...}
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Arquivo de few-shot deve conter uma lista, encontrado: {type(data).__name__}")
    
    examples = []
    for item in data:
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            raise ValueError(f"Cada exemplo few-shot deve ter chaves 'input' e 'output': {item}")
        examples.append({
            "input": item["input"],
            "output": item["output"]
        })
    
    return examples


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_prompt: int
    tokens_completion: int
    latency_ms: float


class LLMClient:
    """Cliente unificado para OpenAI, Anthropic, Google Gemini, Ollama, etc."""
    
    def __init__(self, provider: str = "openai", model: str = None):
        self.provider = provider
        self.model = model or self._default_model(provider)
    
    def _default_model(self, provider: str) -> str:
        defaults = {
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
            "google": "gemini-2.5-flash",
            "ollama": "qwen2.5:7b",
        }
        return defaults.get(provider, "gpt-4o")
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        few_shot_examples: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Gera código a partir do prompt."""
        import time
        start = time.time()
        
        if self.provider == "openai":
            response = self._call_openai(system_prompt, user_prompt, few_shot_examples, temperature, max_tokens)
        elif self.provider == "anthropic":
            response = self._call_anthropic(system_prompt, user_prompt, few_shot_examples, temperature, max_tokens)
        elif self.provider == "google":
            response = self._call_google(system_prompt, user_prompt, few_shot_examples, temperature, max_tokens)
        elif self.provider == "ollama":
            response = self._call_ollama(system_prompt, user_prompt, few_shot_examples, temperature, max_tokens)
        elif self.provider == "groq":
            response = self._call_groq(system_prompt, user_prompt, few_shot_examples, temperature, max_tokens)
        else:
            raise ValueError(f"Provider desconhecido: {self.provider}")
        
        latency = (time.time() - start) * 1000
        return LLMResponse(
            content=response["content"],
            model=self.model,
            tokens_prompt=response["tokens_prompt"],
            tokens_completion=response["tokens_completion"],
            latency_ms=latency
        )
    
    def _call_openai(self, system, user, few_shot, temperature, max_tokens):
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        messages = [{"role": "system", "content": system}]
        
        if few_shot:
            for ex in few_shot:
                messages.append({"role": "user", "content": ex["input"]})
                messages.append({"role": "assistant", "content": ex["output"]})
        
        messages.append({"role": "user", "content": user})
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "content": response.choices[0].message.content,
            "tokens_prompt": response.usage.prompt_tokens,
            "tokens_completion": response.usage.completion_tokens
        }
    
    def _call_anthropic(self, system, user, few_shot, temperature, max_tokens):
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        messages = []
        if few_shot:
            for ex in few_shot:
                messages.append({"role": "user", "content": ex["input"]})
                messages.append({"role": "assistant", "content": ex["output"]})
        
        messages.append({"role": "user", "content": user})
        
        response = client.messages.create(
            model=self.model,
            system=system,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "content": response.content[0].text,
            "tokens_prompt": response.usage.input_tokens,
            "tokens_completion": response.usage.output_tokens
        }
    
    def _call_google(self, system, user, few_shot, temperature, max_tokens):
        """
        Chama o Google Gemini via google-generativeai SDK.
        
        A chave da API é lida do .env (Lia/.env) via API_KEY, GEMINI_API_KEY
        ou GOOGLE_API_KEY.
        """
        import google.generativeai as genai
        
        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("API_KEY")
            or os.getenv("GROG_API_KEY")
        )
        if not api_key:
            raise ValueError(
                "Chave da API do Gemini não encontrada. "
                "Defina GEMINI_API_KEY, GROG_API_KEY, GOOGLE_API_KEY ou API_KEY no arquivo .env"
            )
        
        genai.configure(api_key=api_key)
        
        # Monta o prompt completo: system + few-shot + user
        prompt_parts = [system]
        if few_shot:
            for ex in few_shot:
                prompt_parts.append(f"Exemplo de entrada:\n{ex['input']}")
                prompt_parts.append(f"Exemplo de saída:\n{ex['output']}")
        prompt_parts.append(f"Tarefa:\n{user}")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        # Cria o modelo generativo
        model = genai.GenerativeModel(self.model)
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        
        # Extrai contagem de tokens
        tokens_prompt = 0
        tokens_completion = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens_prompt = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            tokens_completion = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
        
        return {
            "content": response.text,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion
        }
    
    def _call_ollama(self, system, user, few_shot, temperature, max_tokens):
        """Chama modelo local via Ollama (API compatível com OpenAI)."""
        from openai import OpenAI
        
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        client = OpenAI(base_url=base_url, api_key="ollama")
        
        messages = [{"role": "system", "content": system}]
        
        if few_shot:
            for ex in few_shot:
                messages.append({"role": "user", "content": ex["input"]})
                messages.append({"role": "assistant", "content": ex["output"]})
        
        messages.append({"role": "user", "content": user})
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        # A API do Ollama retorna prompt_eval_count e eval_count
        usage = response.usage
        tokens_prompt = getattr(usage, "prompt_tokens", 0) or getattr(usage, "prompt_eval_count", 0)
        tokens_completion = getattr(usage, "completion_tokens", 0) or getattr(usage, "eval_count", 0)
        
        return {
            "content": response.choices[0].message.content,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion
        }
    
    def _call_groq(self, system, user, few_shot, temperature, max_tokens):
        """Chama Groq API (usa cliente dedicado)."""
        from runners.groq_client import GroqClient
        
        client = GroqClient(model=self.model)
        return client.generate(system, user, few_shot, temperature, max_tokens)
