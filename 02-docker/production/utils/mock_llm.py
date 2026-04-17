"""
Mock LLM for Docker production example.
"""
import random
import time

MOCK_RESPONSES = {
    "default": [
        "Day la cau tra loi tu AI agent (mock).",
        "Agent dang hoat dong tot! (mock response)",
        "Toi la AI agent duoc deploy len cloud.",
    ],
    "docker": ["Container la cach dong goi app de chay o moi noi."],
    "deploy": ["Deployment la qua trinh dua code len server."],
    "health": ["Agent dang hoat dong binh thuong."],
}


def ask(question: str, delay: float = 0.1) -> str:
    """Return a mock answer with a small artificial latency."""
    time.sleep(delay + random.uniform(0, 0.05))

    question_lower = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in question_lower:
            return random.choice(responses)

    return random.choice(MOCK_RESPONSES["default"])
