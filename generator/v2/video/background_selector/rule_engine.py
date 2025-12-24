# generator/v2/video/background_selector/rule_engine.py

class BackgroundRuleEngine:

    def __init__(self, rules, fallback):
        self.rules = sorted(
            rules,
            key=lambda r: r["priority"],
            reverse=True,
        )
        self.fallback = fallback

    def resolve(self, text: str) -> str:
        t = text.lower()

        for rule in self.rules:
            if any(k in t for k in rule["keywords"]):
                return rule["category"]

        return self.fallback
