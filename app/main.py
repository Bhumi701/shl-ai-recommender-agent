from fastapi import FastAPI, HTTPException
from app.schemas import ChatRequest, ChatResponse, Recommendation
from app.agent import run_agent

app = FastAPI(title="SHL Assessment Recommender")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")

    messages = [
        {"role": m.role, "content": m.content}
        for m in request.messages
    ]

    if len(messages) > 8:
        return ChatResponse(
            reply="Maximum conversation length reached.",
            recommendations=[],
            end_of_conversation=True,
        )

    result = run_agent(messages)

    recommendations = [
        Recommendation(name=r["name"], url=r["url"], test_type=r.get("test_type", ""))
        for r in result.get("recommendations", [])
    ]

    return ChatResponse(
        reply=result["reply"],
        recommendations=recommendations,
        end_of_conversation=result["end_of_conversation"],
    )