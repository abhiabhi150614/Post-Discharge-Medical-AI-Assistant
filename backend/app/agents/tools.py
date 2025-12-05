from langchain_core.tools import tool
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models import Patient, AgentEvent
from ..rag.retriever import rag_query
import json
import datetime

@tool
def patient_db_tool(name: str):
    """
    Searches for a patient by name in the database.
    Returns patient details if found, or status 'not_found' or 'multiple'.
    """
    db: Session = SessionLocal()
    try:
        print(f"DEBUG: Searching for patient: '{name}'")
        # Clean the input name
        clean_name = name.strip().replace(".", "").replace("  ", " ")
        
        # Case insensitive search
        patients = db.query(Patient).filter(Patient.name.ilike(f"%{clean_name}%")).all()
        
        # If not found, try searching by parts (e.g. first name)
        if not patients:
            print(f"DEBUG: Exact match failed for '{clean_name}'. Trying parts.")
            parts = clean_name.split()
            if len(parts) > 0:
                # Try searching for just the first name or last name
                for part in parts:
                    if len(part) > 2: # Avoid short words
                         sub_results = db.query(Patient).filter(Patient.name.ilike(f"%{part}%")).all()
                         if sub_results:
                             print(f"DEBUG: Found match using part '{part}'")
                             patients = sub_results
                             break

        if not patients:
            print("DEBUG: Patient not found.")
            return json.dumps({"status": "not_found"})
        
        if len(patients) > 1:
            print(f"DEBUG: Multiple patients found: {len(patients)}")
            candidates = [{"id": p.id, "name": p.name, "discharge_date": str(p.discharge_date)} for p in patients]
            return json.dumps({"status": "multiple", "candidates": candidates})
        
        p = patients[0]
        print(f"DEBUG: Patient found: {p.name}")
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
        return json.dumps(patient_data)
    except Exception as e:
        print(f"ERROR in patient_db_tool: {e}")
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

@tool
def rag_tool(question: str, patient_context: str = ""):
    """
    Queries the nephrology reference material using RAG.
    Use this for medical questions, diet, symptoms, etc.
    """
    results = rag_query(question, patient_context)
    return json.dumps(results)

@tool
def web_search_tool(query: str):
    """
    Simulates a web search for latest research or news.
    Use this ONLY when the user asks for 'latest', 'new', '2024', etc.
    """
    # STUB implementation
    print(f"STUB WEB SEARCH: {query}")
    
    # Return dummy but realistic results based on keywords
    if "sglt2" in query.lower():
        return json.dumps([
            {
                "title": "SGLT2 Inhibitors in CKD: 2024 Update",
                "snippet": "Dapagliflozin and Empagliflozin show continued benefit in reducing progression of CKD in non-diabetic patients.",
                "url": "https://www.nejm.org/dummy-article-sglt2"
            },
            {
                "title": "New Guidelines for SGLT2 use",
                "snippet": "KDIGO 2024 guidelines recommend SGLT2 inhibitors for all patients with eGFR > 20.",
                "url": "https://kdigo.org/guidelines"
            }
        ])
    
    return json.dumps([
        {
            "title": "Latest Nephrology News",
            "snippet": "Recent studies focus on finerenone and combination therapies.",
            "url": "https://www.kidney.org/news"
        }
    ])

def log_agent_event(session_id: str, agent_name: str, event_type: str, details: dict):
    db: Session = SessionLocal()
    try:
        event = AgentEvent(
            session_id=session_id,
            agent=agent_name,
            event_type=event_type,
            details=details
        )
        db.add(event)
        db.commit()
    except Exception as e:
        print(f"Failed to log event: {e}")
    finally:
        db.close()
