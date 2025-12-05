from typing import TypedDict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .tools import patient_db_tool, log_agent_event
import json

class AgentState(TypedDict):
    session_id: str
    messages: List[dict]
    patient_data: Optional[dict]
    current_agent: str
    handoff_to_clinical: bool
    user_name: Optional[str]

from .llm import get_llm

llm = get_llm()

RECEPTIONIST_SYSTEM_PROMPT = """You are a hospital receptionist AI for post-discharge kidney patients.
Your goal is to identify the patient and check on their recovery.

Tasks:
1. If you don't know the patient's name, ask for it.
2. Use the 'patient_db_tool' to find their record.
3. Once found, greet them by name and mention their diagnosis to confirm.
4. Ask how they are feeling or if they are taking their meds.
5. If the user asks a MEDICAL question (symptoms, diet, drugs, pain), do NOT answer it. 
   Instead, say you will connect them to the Clinical Agent and set 'handoff_to_clinical' to True.

Current Patient Data: {patient_context}
"""

def receptionist_node(state: AgentState):
    messages = state['messages']
    patient_data = state.get('patient_data')
    
    # Format messages for LLM
    lc_messages = [SystemMessage(content=RECEPTIONIST_SYSTEM_PROMPT.format(
        patient_context=json.dumps(patient_data) if patient_data else "Not identified yet"
    ))]
    
    for m in messages:
        if m['role'] == 'user':
            lc_messages.append(HumanMessage(content=m['content']))
        else:
            lc_messages.append(AIMessage(content=m['content']))

    # Bind tools
    llm_with_tools = llm.bind_tools([patient_db_tool])
    
    # Invoke
    response = llm_with_tools.invoke(lc_messages)
    
    # Handle tool calls
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call['name'] == 'patient_db_tool':
                # Execute tool
                result_json = patient_db_tool.invoke(tool_call['args'])
                result = json.loads(result_json)
                
                log_agent_event(state['session_id'], "receptionist", "db_lookup", tool_call['args'])
                
                if result.get("status") == "ok":
                    # Patient found
                    return {
                        "patient_data": result,
                        "messages": [
                            {"role": "assistant", "content": f"I found your file, {result['name']}. You were discharged on {result['discharge_date']} for {result['diagnosis']}. How are you feeling today?"}
                        ]
                    }
                elif result.get("status") == "multiple":
                     return {
                        "messages": [{"role": "assistant", "content": "I found multiple patients with that name. Could you please provide your full name or date of birth?"}]
                    }
                else:
                    return {
                        "messages": [{"role": "assistant", "content": "I couldn't find a record with that name. Could you please double-check the spelling?"}]
                    }

    # Check for handoff intent in text if no tool called
    # Simple heuristic or let LLM decide via a structured output/tool? 
    # For POC, let's ask LLM to output a special token or just use a second classification step.
    # Simpler: If LLM says "I will connect you to the Clinical Agent", we detect that.
    
    # Check for handoff intent in text if no tool called
    content = response.content
    
    # Handle list content (e.g. from Gemini/Anthropic)
    if isinstance(content, list):
        content_text = " ".join([block["text"] for block in content if isinstance(block, dict) and block.get("type") == "text"])
    else:
        content_text = str(content)

    handoff = False
    
    # Robust handoff detection
    content_lower = content_text.lower()
    if "clinical agent" in content_lower or "connect you" in content_lower:
        handoff = True
        print(f"DEBUG: Handoff detected in receptionist. Content: {content_text[:50]}...")
        log_agent_event(state['session_id'], "receptionist", "handoff", {"reason": "medical_query"})
    else:
        print(f"DEBUG: No handoff detected. Content: {content_text[:50]}...")

    return {
        "messages": [{"role": "assistant", "content": content_text, "agent": "receptionist"}],
        "handoff_to_clinical": handoff
    }
