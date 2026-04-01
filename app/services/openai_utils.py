from openai import OpenAI
from app.config.settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_question(skills: list) -> str:
    prompt = f"Ask a short interview question based on these skills: {', '.join(skills)}. Make it concise."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_report(transcripts: list) -> str:
    prompt = "Generate a professional interview feedback report based on these answers:\n"
    for item in transcripts:
        prompt += f"Q: {item['question']}\nA: {item['answer']}\nConfidence: {item['confidence']}\n\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content.strip()
