import os

from dotenv import load_dotenv
import mlflow

load_dotenv()


RESERVED_PROMPT_ALIASES = {"latest"}
DEFAULT_PROMPT_ALIAS = "production"


class PromptRegister:
    """Đăng ký và đọc prompt trực tiếp từ MLflow Prompt Registry trên Databricks."""

    def __init__(self):
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "databricks"))
        mlflow.set_registry_uri(os.getenv("MLFLOW_REGISTRY_URI", "databricks-uc"))

    def _prompt_alias_assign(self, prompt_name: str, alias_name: str, version: str | int):
        if alias_name.lower() in RESERVED_PROMPT_ALIASES:
            return
        mlflow.genai.set_prompt_alias(
            name=prompt_name,
            alias=alias_name,
            version=version,
        )

    def register_prompt(
        self,
        prompt_name: str,
        prompt_template: str | list[dict],
        alias_name: str = "production",
        enable: bool = False,
    ):
        if not enable:
            return

        prompt_version = mlflow.genai.register_prompt(prompt_name, prompt_template)
        self._prompt_alias_assign(prompt_name, alias_name, prompt_version.version)

    def load_prompt_template(
        self,
        prompt_name: str,
        version: str | int | None = None,
        alias: str = DEFAULT_PROMPT_ALIAS,
    ):
        """Tải prompt (chưa render) từ MLflow để tầng trên có thể cache lại.

        - version: tải đúng số phiên bản (vd 1).
        - alias: tải theo alias, mặc định "production".

        Trả về đối tượng PromptVersion của MLflow (có ``.format(**variables)``),
        giúp tải template MỘT lần rồi render nhiều lần mà không gọi lại mạng.
        """
        uri = (
            f"prompts:/{prompt_name}/{version}"
            if version is not None
            else f"prompts:/{prompt_name}@{alias}"
        )
        return mlflow.genai.load_prompt(uri)

    def load_prompt(
        self,
        prompt_name: str,
        version: str | int | None = None,
        alias: str = DEFAULT_PROMPT_ALIAS,
        **variables,
    ) -> str | list[dict]:
        """Tải prompt trực tiếp từ MLflow và render với các biến truyền vào.

        - version: tải đúng số phiên bản (vd 1).
        - alias: tải theo alias, mặc định "production".

        Trả về str (prompt dạng text) hoặc list[dict] role/content (prompt dạng chat),
        dùng luôn cho lời gọi LLM mà không cần chuyển đổi qua LangChain.
        """
        prompt = self.load_prompt_template(prompt_name, version=version, alias=alias)
        return prompt.format(**variables)
