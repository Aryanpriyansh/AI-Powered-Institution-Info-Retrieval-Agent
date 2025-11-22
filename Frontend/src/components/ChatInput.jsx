import React, { useRef, useEffect } from "react";
import { Send } from "lucide-react";

const ChatInput = ({
  inputMessage,
  setInputMessage,
  handleSendMessage,
  disabled = false,
}) => {
  const taRef = useRef(null);


  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "40px"; // reset
    ta.style.height = Math.min(160, ta.scrollHeight) + "px";
  }, [inputMessage]);

  const onKeyDown = (e) => {

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && inputMessage.trim()) {
        handleSendMessage();
      }
    }
  };

  const onClickSend = () => {
    if (!disabled && inputMessage.trim()) {
      handleSendMessage();
    }
  };

  return (
    <div className="input-area modern-input-area">
      <div className="chat-input-wrapper arrow-style modern-wrapper">
        <textarea
          ref={taRef}
          className="chat-textarea"
          placeholder="Ask about exams, curriculum, fees, or institutional processes..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={disabled}
          rows={1}
        />

        <button
          className="arrow-send-btn compact modern-send"
          onClick={onClickSend}
          aria-label="Send"
          disabled={disabled || !inputMessage.trim()}
        >
          <Send size={16} strokeWidth={2.2} />
        </button>
      </div>

      <p className="input-footer-text">
        Database-driven responses with fallback to administration contacts
      </p>
    </div>
  );
};

export default ChatInput;
