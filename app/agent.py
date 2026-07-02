import os
import json
from groq import Groq
from dotenv import load_dotenv
from app.catalog import search_catalog

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an SHL Assessment Recommender. 
Always reply in valid JSON format.
Only give recommendations when the user is describing a hiring need (a role, skills, or job description) that catalog assessments can address.
If the user is asking a general/comparison/off-topic question (e.g. "what's the difference between X and Y", salary questions, unrelated topics), answer helpfully in the reply field but keep recommendations empty.
For questions that ask to compare, define, or explain assessment types (not hire for a role), you MUST return an empty recommendations array even if the catalog context contains matching items — this is a strict rule with no exceptions.
IMPORTANT: If your reply text mentions or refers to specific assessments, every one of those assessments MUST also appear in the recommendations array with its exact name and URL from the catalog context. Never mention an assessment in the reply without also including it in recommendations, and never include an assessment that isn't in the catalog context provided.
If no matches or unsure, still give a helpful reply but empty recommendations list."""

def build_catalog_context(query: str) -> str:
    results = search_catalog(query, k=10)
    if not results:
        return "No matching assessments in catalog."
    lines = ["Catalog:"]
    for item in results:
        lines.append(f"{item['name']} | {item['url']} | Type:{item.get('test_type','')}")
    return "\n".join(lines)

def run_agent(messages: list) -> dict:
    query = " ".join(m["content"] for m in messages if m["role"] == "user")
    
    catalog_context = build_catalog_context(query)

    groq_messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + catalog_context}
    ]
    groq_messages += messages[-6:]

    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",   # <--- Smaller & faster model (rate limit kam hoga)
            messages=groq_messages,
            temperature=0,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(resp.choices[0].message.content)

        recs = []
        for r in parsed.get("recommendations", [])[:8]:
            if isinstance(r, dict) and "shl.com" in str(r.get("url", "")):
                recs.append({
                    "name": str(r.get("name","")),
                    "url": str(r.get("url","")),
                    "test_type": str(r.get("test_type","")),
                })

        return {
            "reply": parsed.get("reply", "Here are some suitable assessments."),
            "recommendations": recs,
            "end_of_conversation": False
        }

    except Exception as e:
        print("Groq Error:", str(e))   # <--- ye line important hai
        return {
            "reply": "Something went wrong. Please try again.",
            "recommendations": [],
            "end_of_conversation": False
        }