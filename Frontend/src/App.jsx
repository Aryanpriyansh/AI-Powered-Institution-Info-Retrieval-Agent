
import React, { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatHeader from "./components/ChatHeader";
import Messages from "./components/Messages";
import ChatInput from "./components/ChatInput";
import "./App.css";

export default function App() {

  // useEffect(() => {
  //   document.documentElement.setAttribute("data-theme", "dark"); 
  //   document.querySelectorAll(".app-overlay, .global-overlay, .fullscreen-overlay").forEach(el => el.remove());
  // }, []);

  
  const [messages, setMessages] = useState([
    {
      id: Date.now(),
      text: "Hello! I'm EduBot, your 24/7 academic assistant. I can help you with exam structures, curriculum details, fee information, and institutional processes. How can I assist you today?",
      sender: "bot",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    }
  ]);

  const [inputMessage, setInputMessage] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true); // you can set false if you want closed by default
  const [sending, setSending] = useState(false);

 
  const quickQuestions = [
    { id: 1, iconName: "dollar", text: "Admission & Exams", query: "Which entrance exams are accepted for admission?" },
    { id: 2, iconName: "file", text: "NAAC & Accreditation", query: "Is GAT NAAC accredited?" },
    { id: 3, iconName: "building", text: "Campus Facilities", query: "What facilities are available on campus?" },
    { id: 4, iconName: "home", text: "Hostel Info", query: "Are hostels available for both boys and girls?" },
    { id: 5, iconName: "users", text: "Placements", query: "Which companies visit GAT for recruitment?" }
  ];

  
  const addMessage = (msg) => setMessages(prev => [...prev, msg]);

  const replaceMessageById = (id, newFields) => {
    setMessages(prev => prev.map(m => (m.id === id ? { ...m, ...newFields } : m)));
  };

  // main send logic: shows user msg, adds a processing placeholder, calls backend, replaces placeholder
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || sending) return;

    // user message shown immediately
    const userMsg = {
      id: Date.now() + Math.random(),
      text: inputMessage,
      sender: "user",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };
    addMessage(userMsg);
    setInputMessage("");

    // add placeholder bot message (processing)
    const placeholderId = Date.now() + Math.random();
    addMessage({
      id: placeholderId,
      text: "I'm processing your query.",
      sender: "bot",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    });

    setSending(true);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ user_message: userMsg.text })
      });

      if (!res.ok) {
        // replace placeholder with an error message
        replaceMessageById(placeholderId, {
          text: `Error: server returned ${res.status}`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        });
        return;
      }

      const data = await res.json();
      // expected: { response: "..." } from backend
      replaceMessageById(placeholderId, {
        text: data?.response ?? "No response from server.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      });
    } catch (err) {
      // network / fetch error
      replaceMessageById(placeholderId, {
        text: "Error: Could not reach server. Please try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      });
      console.error("[App] send error:", err);
    } finally {
      setSending(false);
    }
  };

  return (
    // app-container controls the grid (sidebar column + main column)
    <div className={`app-container ${isSidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
      <Sidebar
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        quickQuestions={quickQuestions}
        setInputMessage={setInputMessage}
      />

      <div className="main-content" role="main">
        {/* ChatHeader expected to have menu toggle; pass props */}
        <ChatHeader isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />

        {/* Messages reads the `messages` array and renders them */}
        <Messages messages={messages} />

        {/* ChatInput handles input UI; passes send handler */}
        <ChatInput
          inputMessage={inputMessage}
          setInputMessage={setInputMessage}
          handleSendMessage={handleSendMessage}
          disabled={sending}
        />
      </div>
    </div>
  );
}
