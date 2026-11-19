from helper.prompt.prompt_register import PromptRegister

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from helper.prompt.prompt_register import PromptRegister

test_prompt = [
    {
        "role": "system",
        "content": (
            "[PERSONA] Bạn là một chuyên gia tài chính. Chuyên môn của bạn là phân tích tài chính, kinh tết, chứng khoán, "
            "bao gồm cả các chính sách tiền tệ và đầu tư công.\n"
            "[TASK] Nhận câu hỏi của người dùng. Sau đó trả lời câu hỏi đó "
            "[CONTEXT] Cách bạn trả lời như là một chuyên gia tư vấn tài chính"
            "Tuỳ thuộc vào câu hỏi của người dùng mà bạn sẽ trả lời cho phù hợp"
            "Nếu câu hỏi không liên quan tới tài chính, kinh tế "
            "Bạn không cần suy luận gì cảc, chọn một trong những đáp án dưới đây để trả lời người dùng:\n"
            "1: Câu hỏi của bạn không liên quan tới tài chính, kinh tế\n"
            "2: Cảm ơn đã tương tác, nhưng tôi chỉ có thể trả lời về tài chính, kinh tế"
            "3: Tôi đéo rảnh để trả lời mấy câu hỏi như vậy "
            "4: Mày lừa bố à"
            "Nếu câu hỏi liên quan tời tài chính kinh tế, trả lời bình thường như một chuyên gia tài chính"
            "[FORMAT] {{format_instructions}}\n"
        ),
    },
    {
        "role": "user",
        "content": (
            "Giúp tôi trả lời câu hỏi này: \n\n"
            "question: {{question}}\n"
            "question_context: {{question_context}}\n"
            '"""'
        ),
    },
]

prompt_register = PromptRegister()

prompt_register.register_prompt(
    prompt_name="finance_agent_2026.finance_agent_2026_prompt.test_prompt",
    prompt_template=test_prompt,
    enable=True,
)
