import json
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


def translate_note_content(title, content, target_lang="Chinese"):
    result = llm_generate(
        json.dumps({"title": title, "content": content}, ensure_ascii=False),
        target_lang,
    )
    translated = json.loads(result)
    if (
        not isinstance(translated, dict)
        or not isinstance(translated.get("title"), str)
        or not isinstance(translated.get("content"), str)
    ):
        raise ValueError("Translation response must contain string title and content fields")
    return {"title": translated["title"], "content": translated["content"]}


if __name__ == "__main__":
    test_text = sys.argv[1] if len(sys.argv) > 1 else "How are you?"
    print(llm_generate(test_text))
