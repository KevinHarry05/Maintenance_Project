def detect_category(title: str, description: str) -> str:
    text = (title + " " + description).lower()

    category_keywords = {
        "electrical": ["ac", "electric", "power", "socket", "short circuit", "light", "fan"],
        "plumbing": ["water", "leak", "pipe", "tap", "drain", "toilet"],
        "network": ["wifi", "internet", "network", "router", "lan"],
        "cleaning": ["garbage", "waste", "dirty", "clean", "smell"],
        "infrastructure": ["wall", "door", "window", "ceiling", "floor", "lift", "elevator"],
    }

    for category, words in category_keywords.items():
        if any(word in text for word in words):
            return category

    return "infrastructure"


def calculate_priority(title: str, description: str, category: str | None = None):
    text = (title + " " + description).lower()

    critical_keywords = ["fire", "gas leak", "electric shock", "explosion"]
    high_keywords = ["water leakage", "short circuit", "power failure"]
    medium_keywords = ["fan", "light", "broken", "damage"]

    score = 0.1

    for word in critical_keywords:
        if word in text:
            score = 0.9
            return score, "Critical"

    for word in high_keywords:
        if word in text:
            score = 0.7
            return score, "High"

    for word in medium_keywords:
        if word in text:
            score = 0.5
            return score, "Medium"

    if category == "electrical":
        return 0.4, "Medium"

    return score, "Low"