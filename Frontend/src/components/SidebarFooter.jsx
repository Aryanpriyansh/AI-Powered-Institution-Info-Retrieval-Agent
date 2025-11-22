import React from "react";
import { Phone, Bell } from "lucide-react";

const SidebarFooter = () => (
  <div className="sidebar-footer">
    <div className="sidebar-footer-row">
      <a
        href="mailto:info@gat.ac.in"
        className="footer-chip"
      >
        <Phone />
        <span>Contact Us</span>
      </a>

      <a
        href="https://www.gat.ac.in/"
        target="_blank"
        rel="noopener noreferrer"
        className="footer-chip"
      >
        <Bell />
        <span>Updates</span>
      </a>
    </div>
  </div>
);

export default SidebarFooter;
