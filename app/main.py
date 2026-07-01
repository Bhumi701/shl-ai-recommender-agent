from fastapi import FastAPI, HTTPException
from app.schemas import ChatRequest, ChatResponse, Recommendation
from app.agent import run_agent

app = FastAPI(title="SHL Assessment Recommender")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    messages = []
    for m in request.messages:
        if m.role == "assistant":
            messages.append({"role": "assistant", "content": m.content})
        else:
            messages.append({"role": "user", "content": m.content})
    
    # Inject previous recommendations into last assistant message
    for i, msg in enumerate(request.messages):
        if msg.role == "assistant" and hasattr(msg, 'recommendations'):
            pass  # already in content
    
    if not messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")

    if len(messages) > 8:
        return ChatResponse(
            reply="This conversation has reached the maximum length.",
            recommendations=[],
            end_of_conversation=True,
        )

    result = run_agent(messages)
    recommendations = [
        Recommendation(name=r["name"], url=r["url"], test_type=r["test_type"])
        for r in result.get("recommendations", [])
    ]
    return ChatResponse(
        reply=result["reply"],
        recommendations=recommendations,
        end_of_conversation=result["end_of_conversation"],
    )