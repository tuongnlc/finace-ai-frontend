from helper.prompt.prompt_register import PromptRegister

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from helper.prompt.prompt_register import PromptRegister
from floating_chat_prompt import floating_chat_prompt

prompt_register = PromptRegister()

prompt_register.register_prompt(
    prompt_name="finance_agent_2026.finance_agent_2026_prompt.floating_chat",
    prompt_template=floating_chat_prompt,
    enable=True,
)