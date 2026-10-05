import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "translate_prompt.md"

def llm_generate(user_prompt, target_lang="Chinese"):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in .env")

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8").format(target_lang=target_lang)
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b:free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    test_text = sys.argv[1] if len(sys.argv) > 1 else "How are you?"
    print(llm_generate(test_text))
