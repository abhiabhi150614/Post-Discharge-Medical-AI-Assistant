from typing import TypedDict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from .tools import rag_tool, web_search_tool, log_agent_event
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

CLINICAL_SYSTEM_PROMPT = """You are a Clinical AI assistant for nephrology patients.
You have access to a RAG tool (nephrology reference) and a Web Search tool.

Rules:
1. ALWAYS use the 'rag_tool' for questions about symptoms, diet, medications, or CKD management.
2. ONLY use 'web_search_tool' if the user explicitly asks for "latest research", "new drugs", or "2024 updates".
3. Base your answer strictly on the tool output.
4. Include citations if provided by the tool.
5. ALWAYS end your response with: "This is an AI assistant for educational purposes only. Always consult healthcare professionals for medical advice."

Patient Context: {patient_context}
"""



def clinical_node(state: AgentState):
    try:
        return _clinical_node_impl(state)
    except Exception as e:
        print(f"CRITICAL ERROR in clinical_node: {e}")
        import traceback
        traceback.print_exc()
        return {
            "messages": [{"role": "assistant", "content": f"I encountered a system error: {str(e)}. Please try again.", "agent": "clinical"}]
        }

def _clinical_node_impl(state: AgentState):
    messages = state['messages']
    patient_data = state.get('patient_data')
    
    lc_messages = [SystemMessage(content=CLINICAL_SYSTEM_PROMPT.format(
        patient_context=json.dumps(patient_data) if patient_data else "Unknown"
    ))]
    
    for m in messages:
        if m['role'] == 'user':
            lc_messages.append(HumanMessage(content=m['content']))
        else:
            lc_messages.append(AIMessage(content=m['content']))

    # Ensure the last message is from the user (Gemini requirement for single-turn, but we are sending history)
    # Actually, Gemini just needs alternating roles or correct structure.
    # The error "single turn requests end with a user role" implies we might be sending a history where the last message isn't user?
    # But we append the user message right before calling graph.
    # However, if we have a tool output, we need to be careful.
    
    # Let's inspect messages.
    # If the last message in 'messages' is NOT user, we might have an issue.
    # But we iterate 'messages' from state.
    
    # Filter out empty messages just in case
    lc_messages = [m for m in lc_messages if m.content and str(m.content).strip()]
    
    # If the very last message is NOT HumanMessage, we might have a problem if the model expects a user prompt to continue.
    # But usually chat models are fine with history.
    # The specific error "single turn requests end with a user role" suggests it thinks this is a single turn or the structure is wrong.
    
    # Let's make sure we don't send system message as the ONLY message if possible (though we have user msg).
    
    llm_with_tools = llm.bind_tools([rag_tool, web_search_tool])
    
    try:
        response = llm_with_tools.invoke(lc_messages)
    except Exception as e:
        print(f"LLM Invoke Error: {e}")
        # Fallback: try sending just the last user message if history is causing issues
        if messages:
            last_user_msg = [m for m in messages if m['role'] == 'user'][-1]
            fallback_msgs = [
                SystemMessage(content=CLINICAL_SYSTEM_PROMPT.format(
                    patient_context=json.dumps(patient_data) if patient_data else "Unknown"
                )),
                HumanMessage(content=last_user_msg['content'])
            ]
            response = llm_with_tools.invoke(fallback_msgs)
        else:
            raise e
    
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            log_agent_event(state['session_id'], "clinical", tool_name, tool_args)
            
            if tool_name == 'rag_tool':
                # Pass patient context to RAG
                if patient_data:
                    tool_args['patient_context'] = f"Diagnosis: {patient_data.get('diagnosis')}, Meds: {patient_data.get('medications')}"
                
                result_json = rag_tool.invoke(tool_args)
                result = json.loads(result_json)
                
                # Generate final answer based on RAG result
                rag_messages = lc_messages + [
                    AIMessage(content="", tool_calls=[tool_call]),
                    HumanMessage(content=f"Tool Output: {result_json}")
                ]
                final_response = llm.invoke(rag_messages)
                return {
                    "messages": [{"role": "assistant", "content": final_response.content, "agent": "clinical"}]
                }

            elif tool_name == 'web_search_tool':
                result_json = web_search_tool.invoke(tool_args)
                
                web_messages = lc_messages + [
                    AIMessage(content="", tool_calls=[tool_call]),
                    HumanMessage(content=f"Tool Output: {result_json}")
                ]
                final_response = llm.invoke(web_messages)
                return {
                    "messages": [{"role": "assistant", "content": final_response.content, "agent": "clinical"}]
                }

    # If no tool called, just chat (but prompt says MUST use tools for medical stuff)
    return {
        "messages": [{"role": "assistant", "content": response.content, "agent": "clinical"}]
    }
