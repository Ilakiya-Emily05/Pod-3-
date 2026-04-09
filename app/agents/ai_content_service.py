from app.agents.vocab_agent import VocabAgent


class AIContentService:
    def __init__(self):
        self.agent = VocabAgent()

    async def generate_words(
        self,
        industry: str,
        cefr_level: str,
        count: int = 10
    ):
        words = await self.agent.generate(
            industry=industry,
            cefr_level=cefr_level,
            count=count
        )

        # 🔥 validation layer
        cleaned = []

        for w in words:
            if not w.get("word") or not w.get("definition"):
                continue

            cleaned.append({
                "word": w["word"].strip(),
                "definition": w["definition"].strip(),
                "part_of_speech": w.get("part_of_speech"),
                "example_sentence": w.get("example_sentence"),
            })

        return cleaned