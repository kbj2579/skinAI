import { colors, radius } from '../theme'

interface LineProps {
  width?: string | number
  height?: number
  mb?: number
  borderRadius?: number
}

export function SkeletonLine({ width = '100%', height = 14, mb = 0, borderRadius }: LineProps) {
  return (
    <div
      style={{
        width,
        height,
        borderRadius: borderRadius ?? height / 2,
        marginBottom: mb,
        background: `linear-gradient(90deg, ${colors.bgSecondary} 25%, #F0F0F5 50%, ${colors.bgSecondary} 75%)`,
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.4s ease-in-out infinite',
        flexShrink: 0,
      }}
    />
  )
}

export function SkeletonCard({ height = 72 }: { height?: number }) {
  return (
    <div
      style={{
        height,
        borderRadius: radius.xl,
        background: `linear-gradient(90deg, ${colors.bgSecondary} 25%, #F0F0F5 50%, ${colors.bgSecondary} 75%)`,
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.4s ease-in-out infinite',
        marginBottom: 12,
      }}
    />
  )
}

export function SkeletonRecordItem({ last = false }: { last?: boolean }) {
  return (
    <div
      style={{
        padding: '14px 16px',
        borderBottom: last ? 'none' : `1px solid ${colors.divider}`,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <div style={{ flex: 1 }}>
        <SkeletonLine width="55%" height={15} mb={8} />
        <SkeletonLine width="38%" height={11} />
      </div>
      <SkeletonLine width={48} height={24} borderRadius={12} />
    </div>
  )
}

export function SkeletonRecordList({ count = 5 }: { count?: number }) {
  return (
    <div
      style={{
        backgroundColor: colors.card,
        borderRadius: radius.xl,
        overflow: 'hidden',
        boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
      }}
    >
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonRecordItem key={i} last={i === count - 1} />
      ))}
    </div>
  )
}

export function SkeletonDetailCard() {
  return (
    <div style={{ padding: '20px 16px 100px', backgroundColor: colors.bg }}>
      <SkeletonLine width="45%" height={22} mb={8} />
      <SkeletonLine width="32%" height={13} mb={24} />
      <SkeletonCard height={64} />
      <SkeletonCard height={160} />
      <SkeletonCard height={200} />
    </div>
  )
}
