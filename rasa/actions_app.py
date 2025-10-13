from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Promogo Actions API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ActionRequest(BaseModel):
    next_action: str
    sender_id: str
    tracker: dict
    domain: dict

class ActionResponse(BaseModel):
    events: list
    responses: list

@app.get("/")
async def root():
    return {"message": "Promogo Actions API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook", response_model=ActionResponse)
async def action_webhook(request: ActionRequest):
    """
    Simple actions webhook that mimics Rasa's actions server
    """
    try:
        action_name = request.next_action
        
        # Simple action responses
        if action_name == "action_greet":
            return ActionResponse(
                events=[],
                responses=[{"text": "Hello! Welcome to Promogo!"}]
            )
        elif action_name == "action_help":
            return ActionResponse(
                events=[],
                responses=[{"text": "I'm here to help! What do you need assistance with?"}]
            )
        else:
            return ActionResponse(
                events=[],
                responses=[{"text": "Action executed successfully."}]
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5055))
    uvicorn.run("actions_app:app", host="0.0.0.0", port=port, reload=True)
