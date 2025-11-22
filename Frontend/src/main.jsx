// src/main.jsx
console.log('🟢 main.jsx loaded — React starting');

import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css'; // ensure this import points to your stylesheet

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
