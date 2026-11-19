"""Test: load prompt từ MLflow và dùng trực tiếp cho lời gọi LLM."""
from time import time
import sys
from pathlib import Path

# Đưa project root vào sys.path để chạy trực tiếp file này.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import os

from dotenv import load_dotenv
from openai import OpenAI

from helper.prompt.prompt_register import PromptRegister

load_dotenv()

PROMPT_NAME = "finance_agent_2026.finance_agent_2026_prompt.test_prompt"
MODEL = "ai_gateway.llm_model.gpt_oss_20b"
BASE_URL = "https://dbc-a4257ab8-9fcb.cloud.databricks.com/ai-gateway/mlflow/v1"


def build_messages() -> list[dict]:
    """Load prompt từ MLflow và render với các biến truyền vào."""
    register = PromptRegister()
    start_time = time()
    prompt = register.load_prompt(
        PROMPT_NAME,
        format_instructions='Return JSON: {"answer": "<string>", "confidence": <number>}',
        question="Xu hướng lãi suất của Techcombank năm 2026?",
        question_context=(
            "Techcombank dự kiến giữ nguyên lãi suất huy động trong nửa đầu 2026, "
            "nhưng có thể điều chỉnh tăng nhẹ ở nửa cuối năm."
        ),
    )
    end_time = time()
    print(f"Load prompt time: {end_time - start_time:.4f} seconds")
    return prompt



def call_llm(messages: list[dict]) -> None:
    """Stream kết quả LLM ra màn hình qua Databricks AI Gateway."""
    start_time = time()
    client = OpenAI(api_key=os.getenv("DATABRICKS_TOKEN"), base_url=BASE_URL)
    end_time = time()
    print(f"Create LLM client time: {end_time - start_time:.4f} seconds")

    start_time = time()
    stream = client.chat.completions.create(model=MODEL, messages=messages, stream=True)
    end_time = time()
    print(f"Call LLM time: {end_time - start_time:.4f} seconds")
    for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="", flush=True)
    print()


def main() -> None:
    messages = build_messages()

    print("\nKết quả LLM:")
    call_llm(messages)


if __name__ == "__main__":
    main()
