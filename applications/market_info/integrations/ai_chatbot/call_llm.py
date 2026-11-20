"""
Client tích hợp AI cho AI Chatbot: load prompt từ MLflow và gọi LLM.

Luồng xử lý: render prompt đã đăng ký trên MLflow Prompt Registry bằng các
biến truyền vào -> gọi LLM qua Databricks AI Gateway (OpenAI-compatible) ->
trả về kết quả. Hiện tại KHÔNG lưu kết quả vào database.
"""

from __future__ import annotations

import os
from typing import Iterator

from dotenv import load_dotenv
from openai import OpenAI

from config import get_secret
from helper.prompt.prompt_register import PromptRegister

load_dotenv()


# ---------------------------------------------------------------------------
# Databricks AI Gateway configuration
# ---------------------------------------------------------------------------
DEFAULT_PROMPT_NAME = "finance_agent_2026.finance_agent_2026_prompt.floating_chat"
DEFAULT_MODEL = "ai_gateway.llm_model.test_qwen"
DEFAULT_FORMAT_INSTRUCTIONS = (
    "Trả lời trực tiếp bằng văn bản thuần, không bọc JSON hay code block."
)
# Giới hạn token sinh ra để chặn model reasoning lặp vô hạn (loop).
DEFAULT_MAX_TOKENS = 2048


def _extract_text(content) -> str:
    """Lấy phần văn bản từ nội dung model trả về.

    Model reasoning trả ``content`` dạng list các block (vd
    ``{"type": "reasoning", ...}`` cho phần suy luận, ``{"type": "text", ...}``
    cho câu trả lời thật). Hàm này bỏ block reasoning, chỉ giữ lại text.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return ""


def _setting(name: str) -> str | None:
    """Đọc cấu hình Databricks: ưu tiên biến môi trường, fallback secrets.toml."""
    return os.environ.get(name) or get_secret(name)


def _require(name: str, default: str | None = None) -> str:
    value = _setting(name) or default
    if not value:
        raise RuntimeError(
            f"Thiếu cấu hình '{name}'. Khai báo trong biến môi trường "
            f"hoặc .streamlit/secrets.toml."
        )
    return value


def ai_gateway_base_url() -> str:
    """Base URL của Databricks AI Gateway (OpenAI-compatible)."""
    base = _setting("DATABRICKS_AI_GATEWAY_BASE_URL")
    if base:
        return base
    return f"{_require('DATABRICKS_HOST').rstrip('/')}/ai-gateway/mlflow/v1"


class LLMClient:
    """Client gọi LLM cho AI Chatbot qua Databricks AI Gateway.

    Load prompt đã render từ MLflow Prompt Registry rồi gọi LLM để lấy câu trả
    lời. Không ghi kết quả vào database.
    """

    def __init__(
        self,
        prompt_name: str = DEFAULT_PROMPT_NAME,
        model: str = DEFAULT_MODEL,
        timeout: int = 60,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self.prompt_name = prompt_name
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self._register = PromptRegister()
        self._client: OpenAI | None = None

    # -- internal ---------------------------------------------------------
    def _get_client(self) -> OpenAI:
        """Khởi tạo (lazy) OpenAI client trỏ tới Databricks AI Gateway."""
        if self._client is None:
            self._client = OpenAI(
                api_key=_require("DATABRICKS_TOKEN"),
                base_url=ai_gateway_base_url(),
                timeout=self.timeout,
            )
        return self._client

    def load_prompt_template(self):
        """Tải prompt template (chưa render) từ MLflow để tầng gọi cache lại.

        Trả về đối tượng PromptVersion của MLflow, có thể gọi ``.format(**vars)``
        nhiều lần mà không cần gọi lại mạng.
        """
        return self._register.load_prompt_template(self.prompt_name)

    def build_messages(
        self,
        *,
        question: str,
        question_context: str | None = None,
        format_instructions: str = DEFAULT_FORMAT_INSTRUCTIONS,
        prompt_template=None,
    ) -> list[dict]:
        """Render prompt (dùng template đã cache nếu có) với dữ liệu truyền vào."""
        if prompt_template is None:
            prompt_template = self.load_prompt_template()
        prompt = prompt_template.format(
            format_instructions=format_instructions,
            question=question,
            question_context=question_context,
        )
        # Prompt dạng text được bọc thành 1 message để dùng chung cho chat API.
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        return prompt

    # -- operations -------------------------------------------------------
    def complete(
        self,
        *,
        question: str,
        question_context: str | None = None,
        format_instructions: str = DEFAULT_FORMAT_INSTRUCTIONS,
        prompt_template=None,
    ) -> str:
        """Gọi LLM và trả về câu trả lời hoàn chỉnh (không stream)."""
        messages = self.build_messages(
            question=question,
            question_context=question_context,
            format_instructions=format_instructions,
            prompt_template=prompt_template,
        )
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
        )
        return _extract_text(response.choices[0].message.content)

    def stream(
        self,
        *,
        question: str,
        question_context: str | None = None,
        format_instructions: str = DEFAULT_FORMAT_INSTRUCTIONS,
        prompt_template=None,
    ) -> Iterator[str]:
        """Gọi LLM và stream dần từng đoạn nội dung trả về."""
        messages = self.build_messages(
            question=question,
            question_context=question_context,
            format_instructions=format_instructions,
            prompt_template=prompt_template,
        )
        response_stream = self._get_client().chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            max_tokens=self.max_tokens,
        )
        for chunk in response_stream:
            # Bỏ các block reasoning (content dạng list), chỉ stream text thật.
            content = _extract_text(chunk.choices[0].delta.content)
            if content:
                yield content
