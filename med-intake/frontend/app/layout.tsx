import '@astryxdesign/core/reset.css';
import '@astryxdesign/core/astryx.css';
import '../src/themes/neutral/neutral.css';
import {Theme} from '@astryxdesign/core/theme';
import {neutralTheme} from '../src/themes/neutral/neutral';

export const metadata = {
  title: 'Med-Intake Triage',
  description: 'Voice triage intake dashboard',
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en">
      <body>
        <Theme theme={neutralTheme}>{children}</Theme>
      </body>
    </html>
  );
}
