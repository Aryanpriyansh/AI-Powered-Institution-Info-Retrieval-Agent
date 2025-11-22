import React from 'react';

const QuickQuestions = ({ quickQuestions, setInputMessage }) => (
  <div className="sidebar-content">
    <h3 className="quick-questions-title">Quick Questions</h3>
    <div className="quick-questions">
      {quickQuestions.map((item, index) => (
        <button
          key={index}
          onClick={() => setInputMessage(item.query)}
          className="quick-question-btn"
        >
          <span className="quick-question-icon">{item.icon}</span>
          <span className="quick-question-text">{item.text}</span>
        </button>
      ))}
    </div>
  </div>
);

export default QuickQuestions;
