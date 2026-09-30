import '@astryxdesign/core/reset.css';
import '@astryxdesign/core/astryx.css';
import '../src/themes/neutral/neutral.css';
import './logo-swap.css';
import AppThemeProvider from './theme-provider';

export const metadata = {
  title: 'MedLine AI — Triage Console',
  description: 'Voice-first medical intake and triage for Africa',
  icons: {
    icon: '/assets/slogo.png',
    apple: '/assets/slogo.png',
  },
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en">
      <body>
        <AppThemeProvider>{children}</AppThemeProvider>
      </body>
    </html>
  );
}
