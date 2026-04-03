# app/services/prompts.py

PRONUNCIATION_PROMPT_TEMPLATE = """
Generate {num_questions} sentence(s) suitable for pronunciation practice 
for a learner with {difficulty} level English. 

Return a JSON array of objects, each with the following fields:
  - "difficulty": the difficulty level (easy/medium/hard)
  - "question": the sentence for practice

Do not include any other text or explanations. Only output valid JSON.
"""