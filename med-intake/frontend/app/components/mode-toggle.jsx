'use client';

import {MoonIcon, SunIcon} from 'lucide-react';
import {useEffect, useState} from 'react';
import {useThemeMode} from '../theme-provider';

export default function ModeToggle() {
  const {mode, toggle} = useThemeMode();
  const [dark, setDark] = useState(false);

  useEffect(() => {
    if (mode === 'dark') {
      setDark(true);
      return;
    }
    if (mode === 'light') {
      setDark(false);
      return;
    }
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    setDark(mq.matches);
    const fn = e => setDark(e.matches);
    mq.addEventListener('change', fn);
    return () => mq.removeEventListener('change', fn);
  }, [mode]);

  return (
    <button
      onClick={toggle}
      aria-label="Toggle color mode"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 'var(--spacing-8)',
        height: 'var(--spacing-8)',
        borderRadius: 'var(--radius-element)',
        border: '1px solid var(--color-border)',
        backgroundColor: 'var(--color-background-surface)',
        color: 'var(--color-text-primary)',
        cursor: 'pointer',
      }}>
      {dark ? <SunIcon size={16} /> : <MoonIcon size={16} />}
    </button>
  );
}
