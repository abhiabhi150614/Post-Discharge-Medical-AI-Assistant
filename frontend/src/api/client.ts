export interface ChatResponse {
  session_id: string;
  reply: string;
  agent: string;
  citations: string[];
  source_type: string;
}

export async function sendMessage(sessionId: string | null, message: string): Promise<ChatResponse> {
  const res = await fetch("http://localhost:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  
  if (!res.ok) {
    throw new Error("Failed to send message");
  }
  
  return res.json();
}
