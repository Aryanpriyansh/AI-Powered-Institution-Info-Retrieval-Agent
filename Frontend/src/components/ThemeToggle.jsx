import React, { useEffect, useState } from 'react';
import './Theme-toggle.css';

export default function ThemeToggle({ className = '' }) {
  const getInitial = () => {
    try {
      const saved = localStorage.getItem('theme');
      if (saved === 'dark' || saved === 'light') return saved;
      return 'light';
    } catch {
      return 'light';
    }
  };

  const [theme, setTheme] = useState(getInitial);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = theme;
    try {
      localStorage.setItem('theme', theme);
    } catch {}
  }, [theme]);

  const isDark = theme === 'dark';

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <div className={`theme-toggle-root ${className}`}>
      <button
        type="button"
        className={`minimal-toggle ${
          isDark ? 'minimal-toggle--dark' : 'minimal-toggle--light'
        }`}
        onClick={toggleTheme}
        aria-pressed={isDark}
        aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      >
        <span className="minimal-toggle__knob">
          <span className="minimal-toggle__icon">
            {isDark ? '🌙' : '☀️'}
          </span>
        </span>
      </button>
    </div>
  );
}
