import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

const Messages = ({ messages }) => {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div className="messages-area">
      <div className="messages-container" style={{ overflowY: 'auto', flexGrow: 1 }}>
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}


        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default Messages;
