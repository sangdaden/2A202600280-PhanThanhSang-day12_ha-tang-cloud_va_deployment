"""Mock LLM used in the lab so no external API key is required."""
import random
import time


MOCK_RESPONSES = {
    "default": [
        "Day 12 production agent da nhan cau hoi cua ban.",
        "Toi la mock AI agent, san sang ho tro ban tiep.",
        "Cau tra loi nay duoc tao boi mock LLM trong lab.",
    ],
    "docker": ["Docker giup dong goi app de chay nhat quan moi noi."],
    "redis": ["Redis phu hop de luu state stateless giua nhieu instances."],
    "deploy": ["Deployment dua ung dung len moi truong public de phuc vu user."],
}


def ask(question: str, delay: float = 0.08) -> str:
    time.sleep(delay + random.uniform(0, 0.03))
    lower = question.lower()
    for keyword, answers in MOCK_RESPONSES.items():
        if keyword in lower:
            return random.choice(answers)
    return random.choice(MOCK_RESPONSES["default"])
