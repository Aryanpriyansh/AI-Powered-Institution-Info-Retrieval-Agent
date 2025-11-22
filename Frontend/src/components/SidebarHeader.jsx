import React from "react";
import { MessageSquare, X } from "lucide-react";

const SidebarHeader = ({ setIsSidebarOpen }) => (
  <div className="sidebar-header minimal-sidebar-header">
    <div className="sidebar-header-top minimal-header-top">
      <div className="logo-container minimal-logo-container">
        <div className="logo minimal-logo">
          <MessageSquare size={20} color="white" strokeWidth={2} />
        </div>
        <span className="brand minimal-brand">EduBot</span>
      </div>

      <button
        className="close-btn minimal-close-btn"
        onClick={() => setIsSidebarOpen(false)}
        aria-label="Close sidebar"
      >
        <X size={20} />
      </button>
    </div>

    <p className="sidebar-description minimal-description">
      Your AI-powered academic assistant providing 24/7 support for exams,
      curriculum, fees, and institutional queries.
    </p>
  </div>
);

export default SidebarHeader;
