'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

type Mode = 'light' | 'dark';

const ThemeContext = createContext<{ mode: Mode; setMode: (m: Mode) => void }>({
  mode: 'light',
  setMode: () => {},
});

export function useTheme() {
  return useContext(ThemeContext);
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<Mode>('light');

  useEffect(() => {
    const saved = localStorage.getItem('ca-theme') as Mode | null;
    if (saved === 'light' || saved === 'dark') setModeState(saved);
  }, []);

  const setMode = (m: Mode) => {
    setModeState(m);
    localStorage.setItem('ca-theme', m);
  };

  return (
    <ThemeContext.Provider value={{ mode, setMode }}>
      <div data-mode={mode} className="ca-root">
        {children}
      </div>
    </ThemeContext.Provider>
  );
}
