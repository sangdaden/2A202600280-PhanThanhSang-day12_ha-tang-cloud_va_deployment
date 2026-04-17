import random
import time


RESPONSES = [
    "Toi la mock AI agent. Cau hoi cua ban da duoc nhan.",
    "Day la cau tra loi mock, trong production ban co the thay bang OpenAI.",
    "Redis giup luu state de he thong stateless khi scale.",
]


def ask(question: str) -> str:
    time.sleep(0.08)
    if "redis" in question.lower():
        return "Redis duoc dung de luu history va state dung chung giua cac instance."
    return random.choice(RESPONSES)
