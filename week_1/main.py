from groq import Groq
from openai import OpenAI
from appconfig import env_config, CHATBOT_NAME, DEFAULT_SYSTEM_PROMPT


class LLMApp:
    def __init__(self, api_key=None, openai_api_key=None, model="llama-3.3-70b-versatile"):
        self.model = model
        self.conversation_history = []

        if self._is_openai_model(model):
            self.api_key = openai_api_key or env_config.openai_api_key
            if not self.api_key:
                raise ValueError("OpenAI API key required for GPT models")
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.api_key = api_key or env_config.groq_api_key
            if not self.api_key:
                raise ValueError("Groq API key required")
            self.client = Groq(api_key=self.api_key)

    def _is_openai_model(self, model):
        model_lower = model.lower()
        return (any(gpt in model_lower for gpt in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]) or
                model_lower.startswith("openai/"))

    def _is_gpt5_model(self, model):
        model_lower = model.lower()
        return any(gpt in model_lower for gpt in ["gpt-5", "gpt-5-mini", "gpt-5-nano"])

    def chat(self, user_message, system_prompt=None, temperature=0.7, max_tokens=1024):
        messages = [
            {
                "role": "system",
                "content": system_prompt if system_prompt else DEFAULT_SYSTEM_PROMPT
            }
        ]

        if system_prompt:
            messages[0]["content"] = f"You are {CHATBOT_NAME}. {system_prompt}"

        if self.conversation_history:
            messages.extend(self.conversation_history)

        messages.append({"role": "user", "content": user_message})

        if self._is_gpt5_model(self.model):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=max_tokens
            )
        elif self._is_openai_model(self.model):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

        return response.choices[0].message.content


if __name__ == "__main__":
    app = LLMApp()
    message = input("What do you want to ask: ")
    response = app.chat(message)
    print(f"\nAssistant Response: {response}\n")
