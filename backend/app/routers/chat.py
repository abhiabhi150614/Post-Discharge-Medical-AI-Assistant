from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Session as DbSession, Interaction, Patient
from ..schemas import ChatRequest, ChatResponse
from ..agents.graph import graph
import uuid

router = APIRouter()

# In-memory store for graph state (for POC simplicity)
# In production, this would be in Redis or Postgres
graph_state_store = {}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id
    
    # 1. Create session if needed
    if not session_id:
        session_id = str(uuid.uuid4())
        new_session = DbSession(id=session_id)
        db.add(new_session)
        db.commit()
        # Initialize empty state
        graph_state_store[session_id] = {
            "session_id": session_id,
            "messages": [],
            "patient_data": None,
            "current_agent": "receptionist",
            "handoff_to_clinical": False
        }
    
    # 2. Log user message
    user_interaction = Interaction(
        session_id=session_id,
        role="user",
        message=request.message
    )
    db.add(user_interaction)
    db.commit()

    # 3. Retrieve state (try memory first, then DB reconstruction)
    current_state = graph_state_store.get(session_id)
    
    if not current_state:
        # Reconstruct from DB
        print(f"DEBUG: Reconstructing state for {session_id}")
        db_session = db.query(DbSession).filter(DbSession.id == session_id).first()
        if db_session:
            # Fetch interactions
            interactions = db.query(Interaction).filter(Interaction.session_id == session_id).order_by(Interaction.timestamp).all()
            # Note: We exclude the just-added user message from history to avoid duplication if we append it later?
            # Actually, graph expects full history. The user message was just added to DB.
            # So 'interactions' includes the current user message.
            # But the graph logic usually appends the NEW message to the state.
            # So let's reconstruct history EXCLUDING the last one (current request), or just handle it carefully.
            
            # Let's rebuild messages list.
            # The 'current_state' passed to graph should contain the history.
            # Then we append the new message.
            # So we should exclude the *current* message from the reconstructed history if we are going to append it again.
            # But wait, 'interactions' has ALL messages including the one we just inserted at step 2.
            
            messages = []
            # We need to be careful. The current user message is already in DB (step 2).
            # But we want to reconstruct the history BEFORE this message, and then append it.
            # So we exclude the last interaction which is the current user message.
            
            # However, if there are multiple concurrent requests (unlikely for POC), this might be flaky.
            # Better approach: Filter out the specific interaction we just added? 
            # Or just take everything except the last one.
            
            # Let's verify if interactions[-1] is indeed the user message we just added.
            if interactions and interactions[-1].id == user_interaction.id:
                 history_interactions = interactions[:-1]
            else:
                 # This shouldn't happen if we just added it and queried ordered by timestamp
                 history_interactions = interactions

            for i in history_interactions:
                messages.append({"role": i.role, "content": i.message})
            
            # Fetch patient data
            patient_data = None
            if db_session.patient_id:
                p = db.query(Patient).filter(Patient.id == db_session.patient_id).first()
                if p:
                    patient_data = {
                        "status": "ok",
                        "id": p.id,
                        "name": p.name,
                        "discharge_date": str(p.discharge_date),
                        "diagnosis": p.primary_diagnosis,
                        "medications": p.medications,
                        "diet": p.dietary_restrictions,
                        "warning_signs": p.warning_signs,
                        "instructions": p.discharge_instructions
                    }

            # Determine handoff/current agent
            handoff = False
            
            # Look at the last ASSISTANT message to determine state
            # Filter for assistant messages
            asst_msgs = [i for i in interactions[:-1] if i.role == "assistant"]
            if asst_msgs:
                last_asst = asst_msgs[-1]
                if last_asst.agent == "clinical":
                    handoff = True
                elif last_asst.agent == "receptionist":
                    if "clinical agent" in last_asst.message.lower() or "connect you" in last_asst.message.lower():
                        handoff = True
            
            current_state = {
                "session_id": session_id,
                "messages": messages,
                "patient_data": patient_data,
                "current_agent": "clinical" if handoff else "receptionist",
                "handoff_to_clinical": handoff
            }
        else:
            # Fallback (shouldn't happen if session_id is valid)
            current_state = {
                "session_id": session_id,
                "messages": [],
                "patient_data": None,
                "current_agent": "receptionist",
                "handoff_to_clinical": False
            }

    # Append new message (the one we just received)
    current_state["messages"].append({"role": "user", "content": request.message})

    # 4. Invoke Graph
    print(f"DEBUG: Invoking graph. Handoff state: {current_state.get('handoff_to_clinical')}")
    result = graph.invoke(current_state)
    
    # Update state store
    graph_state_store[session_id] = result
    
    # Update DB Session with patient_id if found
    if result.get("patient_data") and result["patient_data"].get("id"):
        db_session = db.query(DbSession).filter(DbSession.id == session_id).first()
        if db_session and not db_session.patient_id:
            db_session.patient_id = result["patient_data"]["id"]
            db.commit()
    
    # Extract response
    last_message = result["messages"][-1]
    reply_content = last_message["content"]
    
    # Handle case where content is a list (e.g. from Anthropic/Gemini)
    if isinstance(reply_content, list):
        # Extract text from blocks
        reply_text = " ".join([block["text"] for block in reply_content if block.get("type") == "text"])
    else:
        reply_text = str(reply_content)
    
    # Determine agent
    agent_name = last_message.get("agent", "receptionist")
    
    # Log assistant message
    asst_interaction = Interaction(
        session_id=session_id,
        role="assistant",
        agent=agent_name,
        message=reply_text
    )
    db.add(asst_interaction)
    db.commit()

    return ChatResponse(
        session_id=session_id,
        reply=reply_text,
        agent=agent_name,
        citations=[], 
        source_type="kb"
    )
