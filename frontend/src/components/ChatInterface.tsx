import React, { useState, useRef, useEffect } from 'react';
import { sendMessage } from '../api/client';
import type { ChatResponse } from '../api/client';
import { Send, Bot, User, Activity, FileText, Search, Info } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
  citations?: string[];
  source_type?: string;
}

export const ChatInterface: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Hello! I'm your post-discharge care assistant. What's your name?", agent: 'receptionist' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const response: ChatResponse = await sendMessage(sessionId, userMsg);
      setSessionId(response.session_id);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.reply, 
        agent: response.agent,
        citations: response.citations,
        source_type: response.source_type
      }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="brand">
            <div className="logo-icon">
              <Activity size={24} />
            </div>
            <div className="brand-text">
              <h1>CareCompanion AI</h1>
              <p>Post-Discharge Support</p>
            </div>
          </div>
          <div className="disclaimer">
            <Info size={14} />
            <span>Educational Purpose Only</span>
          </div>
        </div>
      </header>
      
      {/* Chat Area */}
      <div className="chat-area">
        <div className="messages-container">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className={`avatar ${msg.agent || 'receptionist'}`}>
                  <Bot size={20} />
                </div>
              )}
              
              <div className="message-content">
                <div className="message-bubble">
                  {msg.role === 'assistant' && msg.agent && (
                    <div className="agent-header">
                      <span>{msg.agent === 'receptionist' ? 'Receptionist' : 'Clinical Agent'}</span>
                      {msg.source_type === 'web' && (
                        <span className="source-badge">
                          <Search size={12} /> Web
                        </span>
                      )}
                      {msg.source_type === 'kb' && msg.agent === 'clinical' && (
                        <span className="source-badge">
                          <FileText size={12} /> Reference
                        </span>
                      )}
                    </div>
                  )}
                  <div>{msg.content}</div>
                </div>

                {/* Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="citations">
                    <p className="citations-title">
                      <FileText size={12} /> Sources:
                    </p>
                    <ul>
                      {msg.citations.map((cite, i) => (
                        <li key={i} title={cite}>{cite}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="avatar user">
                  <User size={20} />
                </div>
              )}
            </div>
          ))}
          
          {loading && (
             <div className="loading-indicator">
               <div className="avatar receptionist">
                 <Bot size={20} />
               </div>
               <div className="typing-dots">
                 <div className="dot"></div>
                 <div className="dot"></div>
                 <div className="dot"></div>
               </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="input-area">
        <div className="input-container">
          {/* Quick Prompts */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            {[
              "Hi, I'm John Smith",
              "Hi, I'm Abhishek B Shetty",
              "I have swelling in my legs",
              "Latest research on SGLT2"
            ].map((text, i) => (
              <button
                key={i}
                onClick={() => setInput(text)}
                style={{
                  fontSize: '0.75rem',
                  padding: '0.25rem 0.75rem',
                  backgroundColor: '#f1f5f9',
                  border: '1px solid #e2e8f0',
                  borderRadius: '9999px',
                  cursor: 'pointer',
                  color: '#475569',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#e2e8f0'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#f1f5f9'}
              >
                {text}
              </button>
            ))}
          </div>

          <div className="input-wrapper">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type your message..."
              className="chat-input"
              disabled={loading}
            />
            <button 
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="send-button"
            >
              <Send size={20} />
            </button>
          </div>
          <p className="disclaimer-text">
            AI can make mistakes. Please verify important medical information.
          </p>
        </div>
      </div>
    </div>
  );
};
