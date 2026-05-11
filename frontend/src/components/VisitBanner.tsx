import { colors, font, radius } from '../theme'

export default function VisitBanner({ message }: { message: string }) {
  return (
    <div
      style={{
        backgroundColor: colors.warningLight,
        borderRadius: radius.lg,
        padding: '14px 16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
      }}
    >
      <span style={{ fontSize: 20, flexShrink: 0, marginTop: 1 }}>🏥</span>
      <p style={{ margin: 0, color: colors.warningText, fontSize: font.size.md, lineHeight: 1.5, fontWeight: font.weight.medium }}>
        {message}
      </p>
    </div>
  )
}
