import { colors, font, radius } from '../theme'

type RiskLevel = 'normal' | 'mild' | 'suspicious' | 'danger'

const CONFIG: Record<RiskLevel, { label: string; bg: string; color: string }> = {
  normal:     { label: '정상',      bg: colors.successLight,  color: colors.successText },
  mild:       { label: '경미',      bg: colors.warningLight,  color: colors.warningText },
  suspicious: { label: '주의',      bg: '#FFF0E5',            color: '#B84400' },
  danger:     { label: '위험',      bg: colors.dangerLight,   color: colors.dangerText },
}

export default function RiskBadge({ level }: { level: string }) {
  const cfg = CONFIG[level as RiskLevel] ?? { label: level, bg: colors.bgSecondary, color: colors.text2 }
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '4px 10px',
        borderRadius: radius.pill,
        fontSize: font.size.sm,
        fontWeight: font.weight.semibold,
        backgroundColor: cfg.bg,
        color: cfg.color,
        letterSpacing: '-0.01em',
      }}
    >
      {cfg.label}
    </span>
  )
}
