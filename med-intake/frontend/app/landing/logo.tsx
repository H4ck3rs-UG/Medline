/** MedLine AI logo lockup: phone handset + pulse routing line. Teal + clay, currentColor-free. */
export function MedLineLogo({size = 36}: {size?: number}) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="MedLine AI logo">
      <rect x="2" y="2" width="60" height="60" rx="16" fill="var(--color-accent)" />
      <path
        d="M20 14c-4 1-7 5-7 9 0 12 10 24 24 24 4 0 8-3 9-7l-2-8-7-2-3 4c-3-2-6-5-8-8l4-3-2-7-8-2z"
        fill="var(--color-background-surface)"
      />
      <path
        d="M14 44l7-7 5 5 7-9 5 5 9-11"
        fill="none"
        stroke="var(--color-text-orange)"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function MedLineWordmark({size = 36}: {size?: number}) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--spacing-2)',
        fontFamily: 'ui-rounded, "SF Pro Rounded", "Nunito", system-ui, sans-serif',
        fontWeight: 800,
        fontSize: size * 0.55,
        color: 'var(--color-text-primary)',
      }}>
      <MedLineLogo size={size} />
      MedLine&nbsp;AI
    </span>
  );
}
