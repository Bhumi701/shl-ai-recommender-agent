# SHL Assessment Recommender Agent

A conversational AI agent that recommends relevant SHL assessments based on a hiring need described in natural language — a job role, a required skill set, or a pasted job description.

**Live repo:** https://github.com/Bhumi701/shl-ai-recommender-agent

## Overview

The agent takes a multi-turn conversation as input and returns:
- A natural-language reply
- A list of recommended SHL assessments (name, URL, test type)
- A flag indicating whether the conversation has reached its end

It combines **fuzzy retrieval** over the SHL catalog with an **LLM (Groq — Llama 3.1 8B Instant)** that reasons over the retrieved candidates and the conversation context to produce the final ranked recommendations.

## Architecture

```
User query
    │
    ▼
FastAPI /chat endpoint (main.py)
    │
    ▼
run_agent() (agent.py)
    │
    ├── search_catalog() (catalog.py) — rapidfuzz token_set_ratio retrieval, k=10
    │
    ▼
Groq LLM call (llama-3.1-8b-instant, JSON mode)
    │
    ▼
Validated recommendations (must be shl.com URLs) + reply
```

## Tech Stack

- **FastAPI** — REST API layer, request/response validation via Pydantic
- **Groq (llama-3.1-8b-instant)** — reasoning over retrieved catalog candidates, JSON-mode structured output
- **rapidfuzz** — fuzzy string matching for catalog retrieval (`token_set_ratio`)
- **Pydantic** — schema validation (`schemas.py`)
- **Render** — deployment

## Key Design Decisions

1. **Retrieval before generation:** The full catalog is never sent to the LLM. `search_catalog()` narrows it down to the top-k (k=10) fuzzy-matched candidates first, keeping token usage low and avoiding context overflow on complex/long queries.
2. **JSON-mode output:** The LLM is constrained to `response_format={"type": "json_object"}` so responses are always machine-parseable.
3. **URL validation guardrail:** Every recommendation is checked for `shl.com` in its URL before being returned — this prevents the model from hallucinating assessments that aren't in the catalog.
4. **Refine-context preservation:** Assistant turns' structured recommendations are re-injected into the message content as `[Previously recommended: ...]` before being sent back to the LLM, so multi-turn refinement (e.g. "also add a personality test") retains context that would otherwise be lost when only `role`/`content` are forwarded.
5. **Conversation length cap:** Conversations are capped at 8 messages to bound cost and latency.

## Known Limitations

- Comparison-style queries ("what's the difference between X and Y") can still occasionally trigger recommendations if the catalog fuzzy-match score is high, since the system prompt relies on the LLM's judgment rather than a hard rule.
- Off-topic/prompt-injection handling is tested only for empty recommendations, not for the safety of the reply text itself.
- The fuzzy-match threshold (score > 28) is permissive; on large catalogs this may surface some low-relevance candidates for the LLM to filter.

## Running Locally

```bash
pip install fastapi uvicorn groq rapidfuzz python-dotenv
# set GROQ_API_KEY in a .env file
uvicorn app.main:app --reload --port 8000
python test_traces.py   # runs the local eval suite
```

## API

**POST** `/chat`
```json
{
  "messages": [
    {"role": "user", "content": "I am hiring a Java developer, mid level, 4 years experience"}
  ]
}
```

**Response**
```json
{
  "reply": "...",
  "recommendations": [
    {"name": "...", "url": "https://www.shl.com/...", "test_type": "..."}
  ],
  "end_of_conversation": false
}
```
