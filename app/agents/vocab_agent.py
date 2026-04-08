import json
from langchain.chat_models import ChatOpenAI

from app.prompts.vocab_prompts import build_vocab_prompt


class VocabAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )

    async def generate(
        self,
        industry: str,
        cefr_level: str,
        count: int = 10
    ):
        prompt = build_vocab_prompt(industry, cefr_level, count)

        response = await self.llm.ainvoke(prompt)

        content = response.content

        try:
            data = json.loads(content)
        except Exception:
            return []

        return data