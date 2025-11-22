import React from 'react';
const MessageBubble = ({ message }) => (
  <div className={`message-wrapper ${message.sender === 'user' ? 'message-user' : 'message-bot'}`}>
    <div className={`message ${message.sender === 'user' ? 'message-user-bubble' : 'message-bot-bubble'}`}>
      <p className="message-text">{message.text}</p>
      <span className="message-time">{message.timestamp}</span>
    </div>
  </div>
);

export default MessageBubble;
