'use client';
import { MoonIcon, SunIcon } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useThemeMode } from '../../theme-provider';

export default function ThemeToggle() {
  const { mode, toggle } = useThemeMode();
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
      className="btn glass flex items-center justify-center !px-4 py-3.5"
    >
      {dark ? <SunIcon className="size-4" /> : <MoonIcon className="size-4" />}
    </button>
  );
}
