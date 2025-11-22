import React from "react";
import SidebarHeader from "./SidebarHeader";
import QuickQuestions from "./QuickQuestions";
import SidebarFooter from "./SidebarFooter";

const Sidebar = ({
  isSidebarOpen,
  setIsSidebarOpen,
  quickQuestions,
  setInputMessage,
}) => {
  return (
    <div className={`sidebar ${isSidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
      <SidebarHeader setIsSidebarOpen={setIsSidebarOpen} />

      <div className="sidebar-main">
        <QuickQuestions
          quickQuestions={quickQuestions}
          setInputMessage={setInputMessage}
        />
      </div>


      <SidebarFooter />
    </div>
  );
};

export default Sidebar;
