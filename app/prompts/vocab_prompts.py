def build_vocab_prompt(industry: str, cefr_level: str, count: int) -> str:
    return f"""
Generate {count} vocabulary words for the {industry} industry.

CEFR Level: {cefr_level}

Rules:
- Words must be commonly used in real-world professional contexts
- Avoid rare or obscure words
- Provide clear, concise definitions
- Include a natural example sentence

Return ONLY valid JSON array like:
[
  {{
    "word": "...",
    "definition": "...",
    "part_of_speech": "...",
    "example_sentence": "..."
  }}
]
"""
