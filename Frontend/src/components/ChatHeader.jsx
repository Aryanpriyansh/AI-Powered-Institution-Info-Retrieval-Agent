import React from "react";
import { Menu } from "lucide-react";
import ThemeToggle from "./ThemeToggle";

export default function ChatHeader({ isSidebarOpen, setIsSidebarOpen }) {
  return (
    <header className="main-header">
      {!isSidebarOpen && (
        <button className="menu-btn" onClick={() => setIsSidebarOpen(true)} aria-label="Open sidebar">
          <Menu size={20} />
        </button>
      )}

      <div className="header-info">
        <h1 className="header-title">EduBot Assistant</h1>
        {/* <p className="header-subtitle">Powered by GEMINI API & FAST API</p> */}
      </div>

      <div className="header-controls">

        <ThemeToggle />
      </div>
    </header>
  );
}
