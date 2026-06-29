"use client";

import React, { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { fetchWithAuth } from "@/app/utils/api";

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  thinking: string;
  created_at: string;
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  
  // Trạng thái loading
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [username, setUsername] = useState("");
  const [error, setError] = useState("");
  
  // Trạng thái toggle Accordion cho phần suy nghĩ (key: message_id, value: boolean)
  const [openThinking, setOpenThinking] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Kiểm tra xác thực khi vào trang
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const storedUsername = localStorage.getItem("username");
    
    if (!token) {
      window.location.href = "/";
      return;
    }
    
    setUsername(storedUsername || "Luật sư");
    loadSessions(token);
  }, []);

  // 2. Tự động cuộn xuống khi có tin nhắn mới
  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 3. Tải danh sách phòng chat từ API
  const loadSessions = async (token: string) => {
    setIsLoadingSessions(true);
    setError("");
    try {
      const response = await fetchWithAuth("http://localhost:8000/api/chat/sessions");
      const data = await response.json();
      if (response.ok && data.success) {
        setSessions(data.data);
      } else {
        setError(data.message || "Không thể tải danh sách phòng chat.");
      }
    } catch (err) {
      setError("Lỗi kết nối đến máy chủ.");
    } finally {
      setIsLoadingSessions(false);
    }
  };

  // 4. Tải tin nhắn của phòng chat được chọn
  const loadMessages = async (sessionId: string) => {
    setIsLoadingMessages(true);
    setError("");
    try {
      const response = await fetchWithAuth(`http://localhost:8000/api/chat/sessions/${sessionId}/messages`);
      const data = await response.json();
      if (response.ok && data.success) {
        setMessages(data.data);
        // Reset trạng thái toggle suy nghĩ
        setOpenThinking({});
      } else {
        setError(data.message || "Không thể tải lịch sử tin nhắn.");
      }
    } catch (err) {
      setError("Lỗi kết nối khi tải tin nhắn.");
    } finally {
      setIsLoadingMessages(false);
    }
  };

  // Click chọn phòng chat
  const handleSelectSession = (sessionId: string) => {
    setActiveSessionId(sessionId);
    loadMessages(sessionId);
  };

  // 5. Tạo phòng chat mới
  const handleCreateSession = async (customTitle?: string) => {
    setError("");
    try {
      const response = await fetchWithAuth("http://localhost:8000/api/chat/sessions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          title: customTitle || `Hội thoại #${sessions.length + 1}`
        })
      });
      const data = await response.json();
      if (response.ok && data.success) {
        const newSession = data.data;
        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
        setMessages([]);
        return newSession.id;
      } else {
        setError(data.message || "Không thể tạo cuộc hội thoại mới.");
      }
    } catch (err) {
      setError("Lỗi kết nối khi tạo phòng chat.");
    }
    return null;
  };

  // 6. Xóa phòng chat
  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation(); // Không kích hoạt chọn phòng chat
    if (!confirm("Bạn có chắc chắn muốn xóa cuộc hội thoại này?")) return;

    setError("");
    try {
      const response = await fetchWithAuth(`http://localhost:8000/api/chat/sessions/${sessionId}`, {
        method: "DELETE"
      });
      const data = await response.json();
      if (response.ok && data.success) {
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
          setMessages([]);
        }
      } else {
        setError(data.message || "Không thể xóa phòng chat.");
      }
    } catch (err) {
      setError("Lỗi kết nối khi xóa phòng chat.");
    }
  };

  // 7. Gửi tin nhắn mới
  const handleSendMessage = async (e?: React.FormEvent, textToSend?: string) => {
    if (e) e.preventDefault();
    
    const messageContent = textToSend || inputText;
    if (!messageContent.trim()) return;

    let sessionId = activeSessionId;
    
    // Nếu chưa chọn phòng chat, tự động tạo một phòng mới trước
    if (!sessionId) {
      const createdId = await handleCreateSession(messageContent.substring(0, 30) + "...");
      if (!createdId) return;
      sessionId = createdId;
    }

    setInputText("");
    setIsSending(true);
    setError("");

    // Hiển thị tin nhắn người dùng tạm thời
    const tempUserMsg: ChatMessage = {
      id: "temp_user_msg",
      role: "user",
      content: messageContent,
      thinking: "",
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await fetchWithAuth(`http://localhost:8000/api/chat/sessions/${sessionId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          content: messageContent
        })
      });
      
      if (!response.ok) {
        let errMsg = "Không thể kết nối đến AI Agent.";
        try {
          const errData = await response.json();
          errMsg = errData.message || errMsg;
        } catch (_) {}
        throw new Error(errMsg);
      }

      if (!response.body) {
        throw new Error("Không nhận được dữ liệu stream từ server.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      // Khởi tạo tin nhắn Assistant tạm thời trong danh sách tin nhắn
      const assistantTempId = "temp_assistant_msg_" + Date.now();
      const tempAssistantMsg: ChatMessage = {
        id: assistantTempId,
        role: "assistant",
        content: "",
        thinking: "",
        created_at: new Date().toISOString()
      };

      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== "temp_user_msg");
        return [...filtered, tempUserMsg, tempAssistantMsg];
      });

      // Tự động mở accordion suy nghĩ cho tin nhắn đang stream
      setOpenThinking((prev) => ({
        ...prev,
        [assistantTempId]: true
      }));

      let currentThinking = "";
      let currentContent = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        // Giữ lại phần dòng chưa hoàn chỉnh cuối cùng trong buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) continue;
          if (trimmedLine.startsWith("data: ")) {
            const dataStr = trimmedLine.substring(6);
            if (dataStr === "[DONE]") continue;

            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.type === "thinking") {
                currentThinking += parsed.delta;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantTempId
                      ? { ...msg, thinking: currentThinking }
                      : msg
                  )
                );
              } else if (parsed.type === "text") {
                currentContent += parsed.delta;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantTempId
                      ? { ...msg, content: currentContent }
                      : msg
                  )
                );
              } else if (parsed.type === "done") {
                // Nhận thông tin ID và ngày tạo thật từ database
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantTempId
                      ? { ...msg, id: parsed.id, created_at: parsed.created_at }
                      : msg
                  )
                );
                
                // Đồng bộ hóa trạng thái toggle accordion sang ID mới
                setOpenThinking((prev) => {
                  const copy = { ...prev };
                  copy[parsed.id] = copy[assistantTempId];
                  delete copy[assistantTempId];
                  return copy;
                });
              } else if (parsed.type === "error") {
                setError(parsed.message);
              }
            } catch (e) {
              console.error("Lỗi parse SSE line:", trimmedLine, e);
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message || "Lỗi kết nối khi gửi tin nhắn.");
    } finally {
      setIsSending(false);
    }
  };

  // 8. Click câu hỏi gợi ý
  const handleSuggestedClick = async (question: string) => {
    await handleSendMessage(undefined, question);
  };

  // 9. Đăng xuất
  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    window.location.href = "/";
  };

  // Toggle suy nghĩ Accordion
  const toggleThinking = (msgId: string) => {
    setOpenThinking((prev) => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  // Hàm parse markdown sang HTML cơ bản
  const formatMessageHTML = (text: string) => {
    if (!text) return { __html: "" };
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // In đậm **text**
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // Trích dẫn blockquote
    html = html.replace(/^&gt;\s+(.*)$/gm, "<blockquote>$1</blockquote>");
    
    // Danh sách hoa thị * item
    html = html.replace(/^\*\s+(.*)$/gm, "<li>$1</li>");
    
    // Xuống dòng
    html = html.replace(/\n/g, "<br />");
    
    return { __html: html };
  };

  // 4 Câu hỏi mẫu gợi ý
  const suggestedQuestions = [
    {
      title: "Chị H đơn phương nghỉ việc",
      desc: "Chị H nghỉ việc sau 3 ngày do công ty trả lương chậm và thấp hơn mức tối thiểu vùng..."
    },
    {
      title: "Quy định về thử việc",
      desc: "Thời gian thử việc tối đa của kỹ sư công nghệ và quyền đơn phương chấm dứt thử việc..."
    },
    {
      title: "Chậm trả lương 15 ngày",
      desc: "Tôi bị chậm lương quá 15 ngày thì có được nghỉ việc ngay mà không cần báo trước không?"
    },
    {
      title: "Truy thu chênh lệch lương",
      desc: "Cách yêu cầu công ty hoàn trả chênh lệch giữa mức lương thực nhận và mức tối thiểu vùng..."
    }
  ];

  return (
    <div className="chat-layout">
      {/* Nền Blur chuyển động */}
      <div className="bg-container">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>

      {/* 1. Sidebar bên trái */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="sidebar-logo-inner">
              <Image
                src="/logo.jpg"
                alt="RAG Lawyer Logo"
                width={36}
                height={36}
              />
            </div>
          </div>
          <h2>RAG LAWYER</h2>
        </div>

        <div className="new-chat-wrapper">
          <button className="btn-new-chat" onClick={() => handleCreateSession()}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Cuộc hội thoại mới
          </button>
        </div>

        {/* Danh sách phòng chat */}
        <div className="session-list">
          {isLoadingSessions ? (
            <div style={{ textAlign: "center", padding: "20px", color: "var(--text-muted)", fontSize: "14px" }}>
              Đang tải danh sách...
            </div>
          ) : sessions.length === 0 ? (
            <div style={{ textAlign: "center", padding: "20px", color: "var(--text-muted)", fontSize: "13px" }}>
              Chưa có cuộc hội thoại nào.
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${activeSessionId === session.id ? "active" : ""}`}
                onClick={() => handleSelectSession(session.id)}
              >
                <div className="session-title-wrapper">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                  <span className="session-title">{session.title}</span>
                </div>
                <button
                  className="btn-delete-session"
                  onClick={(e) => handleDeleteSession(e, session.id)}
                  title="Xóa cuộc trò chuyện"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer Sidebar (Thông tin User & Logout) */}
        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="user-avatar">
              {username.charAt(0).toUpperCase()}
            </div>
            <div className="user-info">
              <span className="user-name">{username}</span>
              <span className="user-role">Luật sư thành viên</span>
            </div>
          </div>
          <button className="btn-logout" onClick={handleLogout} title="Đăng xuất tài khoản">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        </div>
      </div>

      {/* 2. Vùng chat chính bên phải */}
      <div className="chat-main">
        {/* Header bar của vùng chat */}
        <div className="chat-header-bar">
          <div className="chat-active-title">
            {activeSessionId 
              ? sessions.find((s) => s.id === activeSessionId)?.title || "Đang hội thoại..."
              : "Bảng làm việc RAG Lawyer"
            }
          </div>
          {error && (
            <div style={{ color: "var(--error)", fontSize: "13px", fontWeight: 500 }}>
              ⚠️ {error}
            </div>
          )}
        </div>

        {/* Nội dung tin nhắn hoặc Màn hình chào mừng */}
        {!activeSessionId && messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-logo-wrapper">
              <div className="welcome-logo-inner">
                <Image
                  src="/logo.jpg"
                  alt="RAG Lawyer Logo"
                  width={114}
                  height={114}
                />
              </div>
            </div>
            <h3>Xin chào, tôi là RAG Lawyer</h3>
            <p>
              Tôi là một Trợ lý Pháp lý AI tự trị. Tôi có thể nghiên cứu các bộ luật, phân tích vụ việc thực tế 
              và đề xuất kế hoạch giải quyết tranh chấp lao động có lợi nhất cho bạn.
            </p>
            
            <div className="suggested-questions">
              {suggestedQuestions.map((q, idx) => (
                <div 
                  key={idx} 
                  className="suggested-item"
                  onClick={() => handleSuggestedClick(q.desc)}
                >
                  <h4>{q.title}</h4>
                  <p>{q.desc}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages-list">
            {isLoadingMessages ? (
              <div style={{ display: "flex", flex: 1, alignItems: "center", justifyContent: "center", color: "var(--text-secondary)", gap: "10px" }}>
                <svg className="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
                  <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.1)"></circle>
                  <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor"></path>
                </svg>
                <span>Đang tải lịch sử hội thoại...</span>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div 
                    key={message.id} 
                    className={`message-row ${message.role === "user" ? "user-row" : "assistant-row"}`}
                  >
                    {/* Avatar của tin nhắn */}
                    <div className="message-avatar-wrapper">
                      {message.role === "user" ? (
                        <div className="message-avatar-user">
                          {username.charAt(0).toUpperCase()}
                        </div>
                      ) : (
                        <div className="message-avatar-inner">
                          <Image
                            src="/logo.jpg"
                            alt="AI Avatar"
                            width={38}
                            height={38}
                          />
                        </div>
                      )}
                    </div>

                    {/* Nội dung box tin nhắn */}
                    <div className="message-content-box">
                      {/* Quá trình suy nghĩ của AI (nếu có và thuộc AI message) */}
                      {message.role === "assistant" && message.thinking && (
                        <div className="thinking-container">
                          <div 
                            className={`thinking-header ${openThinking[message.id] ? "open" : ""}`}
                            onClick={() => toggleThinking(message.id)}
                          >
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                              <polyline points="9 18 15 12 9 6"></polyline>
                            </svg>
                            <span>Quá trình lập luận pháp lý của AI...</span>
                          </div>
                          {openThinking[message.id] && (
                            <div className="thinking-body">
                              {message.thinking}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Bong bóng tin nhắn văn bản chính */}
                      <div 
                        className="message-bubble"
                        dangerouslySetInnerHTML={formatMessageHTML(message.content)}
                      />
                    </div>
                  </div>
                ))}
                
                {/* Typing Indicator khi AI đang xử lý */}
                {isSending && (
                  <div className="message-row assistant-row">
                    <div className="message-avatar-wrapper">
                      <div className="message-avatar-inner">
                        <Image
                          src="/logo.jpg"
                          alt="AI Avatar"
                          width={38}
                          height={38}
                        />
                      </div>
                    </div>
                    <div className="message-content-box">
                      <div className="message-bubble" style={{ padding: "8px 12px" }}>
                        <div className="typing-bubble">
                          <div className="typing-dot"></div>
                          <div className="typing-dot"></div>
                          <div className="typing-dot"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        )}

        {/* 3. Ô nhập tin nhắn */}
        <div className="chat-input-area">
          <form className="chat-input-form" onSubmit={(e) => handleSendMessage(e)}>
            <input
              type="text"
              className="chat-input-field"
              placeholder={activeSessionId ? "Nhập câu hỏi pháp lý của bạn tại đây..." : "Nhập câu hỏi để bắt đầu cuộc hội thoại mới..."}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={isSending}
            />
            <button 
              type="submit" 
              className="btn-send-message" 
              disabled={isSending || !inputText.trim()}
            >
              {isSending ? (
                <svg className="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
                  <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.2)"></circle>
                  <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor"></path>
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
