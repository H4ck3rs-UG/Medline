'use client';

import {createContext, useCallback, useContext, useEffect, useState} from 'react';
import {Theme} from '@astryxdesign/core/theme';
import {neutralTheme} from '../src/themes/neutral/neutral';

const MODE_KEY = 'medline-theme-mode';

const ThemeModeContext = createContext({mode: 'system', toggle: () => {}});

export function useThemeMode() {
  return useContext(ThemeModeContext);
}

export default function AppThemeProvider({children}) {
  const [mode, setMode] = useState('system');

  useEffect(() => {
    try {
      const v = localStorage.getItem(MODE_KEY);
      if (v === 'light' || v === 'dark' || v === 'system') setMode(v);
    } catch {}
  }, []);

  const toggle = useCallback(() => {
    setMode(prev => {
      const next = prev === 'dark' ? 'light' : 'dark';
      try {
        localStorage.setItem(MODE_KEY, next);
      } catch {}
      return next;
    });
  }, []);

  return (
    <ThemeModeContext.Provider value={{mode, toggle}}>
      <Theme theme={neutralTheme} mode={mode}>
        {children}
      </Theme>
    </ThemeModeContext.Provider>
  );
}
