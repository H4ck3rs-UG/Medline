/** Flat line-art human illustrations. Teal strokes + clay accents via theme tokens. */
import type {CSSProperties} from 'react';

const TEAL = 'var(--color-accent)';
const CLAY = 'var(--color-text-orange)';
const INK = 'var(--color-text-primary)';

function Fig({children, label, w = 120, h = 120}: {children: React.ReactNode; label: string; w?: number; h?: number}) {
  return (
    <svg width={w} height={h} viewBox="0 0 120 120" role="img" aria-label={label}>
      {children}
    </svg>
  );
}
const stroke = (color: string, width = 4): CSSProperties => ({
  fill: 'none',
  stroke: color,
  strokeWidth: width,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
});

export function PersonCalling() {
  return (
    <Fig label="Person on a phone call">
      <circle cx="60" cy="30" r="14" style={stroke(TEAL)} />
      <path d="M38 108c2-20 10-32 22-32s20 12 22 32" style={stroke(TEAL)} />
      <rect x="76" y="34" width="12" height="24" rx="6" style={stroke(CLAY)} />
      <path d="M94 44l8-8m0 0h-6m6 0v6" style={stroke(CLAY, 3)} />
      <path d="M20 60l6 6 5-5 6 6" style={stroke(CLAY, 3)} />
    </Fig>
  );
}
export function Clinic() {
  return (
    <Fig label="Clinic building">
      <path d="M25 105V55l35-22 35 22v50" style={stroke(TEAL)} />
      <path d="M25 105h70M60 78v-12m-6 6h12" style={stroke(CLAY)} />
      <rect x="42" y="62" width="36" height="43" style={stroke(TEAL)} />
    </Fig>
  );
}
export function Phone() {
  return (
    <Fig label="Mobile phone">
      <rect x="42" y="18" width="36" height="84" rx="10" style={stroke(TEAL)} />
      <path d="M54 28h12" style={stroke(CLAY, 3)} />
      <circle cx="60" cy="88" r="4" style={stroke(CLAY, 3)} />
      <path d="M52 48l4 4 8-9" style={stroke(TEAL, 3)} />
    </Fig>
  );
}
export function MapPin() {
  return (
    <Fig label="Distance map pin">
      <path d="M60 12c-16 0-26 11-26 25 0 18 26 47 26 47s26-29 26-47c0-14-10-25-26-25z" style={stroke(TEAL)} />
      <circle cx="60" cy="38" r="9" style={stroke(CLAY)} />
      <path d="M20 100h80" style={stroke(TEAL, 3)} />
    </Fig>
  );
}
export function ChwDesk() {
  return (
    <Fig label="Community health worker at a desk">
      <circle cx="48" cy="28" r="12" style={stroke(TEAL)} />
      <path d="M30 96c1-16 8-26 18-26s17 10 18 26" style={stroke(TEAL)} />
      <path d="M66 70h40M70 70v26m32-26v26" style={stroke(CLAY)} />
      <rect x="76" y="52" width="20" height="14" rx="2" style={stroke(TEAL, 3)} />
    </Fig>
  );
}
export function Nurse() {
  return (
    <Fig label="Nurse at a clinic">
      <circle cx="60" cy="26" r="13" style={stroke(TEAL)} />
      <path d="M52 14l8-6 8 6" style={stroke(CLAY, 3)} />
      <path d="M40 106c2-22 10-34 20-34s18 12 20 34" style={stroke(TEAL)} />
      <path d="M60 72v10m-5-5h10" style={stroke(CLAY, 3)} />
    </Fig>
  );
}
export function FeaturePhone() {
  return (
    <Fig label="Person holding a basic feature phone">
      <circle cx="46" cy="30" r="13" style={stroke(TEAL)} />
      <path d="M28 106c2-18 9-28 18-28 4 0 8 2 11 5" style={stroke(TEAL)} />
      <rect x="66" y="52" width="22" height="40" rx="5" style={stroke(CLAY)} />
      <path d="M72 60h10M72 66h10M72 72h10" style={stroke(TEAL, 2.5)} />
      <circle cx="77" cy="84" r="3" style={stroke(CLAY, 2.5)} />
    </Fig>
  );
}
export function Listening() {
  return (
    <Fig label="Person listening">
      <circle cx="60" cy="32" r="14" style={stroke(TEAL)} />
      <path d="M38 108c2-20 10-32 22-32s20 12 22 32" style={stroke(TEAL)} />
      <path d="M92 40a14 14 0 010 20M98 32a24 24 0 010 34" style={stroke(CLAY, 3)} />
    </Fig>
  );
}
export function Inked({d, w = 120}: {d: string; w?: number}) {
  return (
    <Fig label="Illustration" w={w} h={w}>
      <path d={d} style={{...stroke(INK), opacity: 0.85}} />
    </Fig>
  );
}
