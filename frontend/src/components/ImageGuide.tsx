import { colors, font, radius, shadow } from '../theme'

type AnalysisType = 'skin' | 'scalp' | 'lesion'

const GUIDES: Record<AnalysisType, string[]> = {
  skin: [
    '세안 후 30분 뒤 자연광 아래에서 촬영하세요.',
    '분석 부위가 화면 중앙에 오도록 하세요.',
    '선명하게 초점을 맞추고 15~20cm 거리를 유지하세요.',
  ],
  scalp: [
    '두피 전용 카메라 또는 근접 촬영 모드를 사용하세요.',
    '모발을 가르마로 나눠 두피가 잘 보이게 하세요.',
    '밝은 조명 아래에서 촬영하세요.',
  ],
  lesion: [
    '점/병변이 화면 중앙에 오도록 하세요.',
    '자 또는 동전을 옆에 두어 크기 비교가 가능하게 하세요.',
    '여러 각도에서 촬영하면 정확도가 높아집니다.',
  ],
}

const TYPE_KO: Record<AnalysisType, string> = { skin: '안면피부', scalp: '두피', lesion: '병변' }

export default function ImageGuide({ type, onClose }: { type: AnalysisType; onClose: () => void }) {
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: colors.card,
          borderRadius: `${radius.xl}px ${radius.xl}px 0 0`,
          padding: '8px 24px 32px',
          width: '100%',
          maxWidth: 390,
          boxShadow: shadow.modal,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 핸들 */}
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 12, marginBottom: 20 }}>
          <div style={{ width: 36, height: 4, backgroundColor: colors.border, borderRadius: 2 }} />
        </div>

        <h3
          style={{
            fontSize: font.size.lg,
            fontWeight: font.weight.bold,
            color: colors.text1,
            marginBottom: 4,
            letterSpacing: '-0.01em',
          }}
        >
          촬영 가이드
        </h3>
        <p style={{ fontSize: font.size.sm, color: colors.text2, marginBottom: 20 }}>
          {TYPE_KO[type]} 분석을 위한 팁
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
          {GUIDES[type].map((g, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 12,
                backgroundColor: colors.bg,
                borderRadius: radius.md,
                padding: '12px 14px',
              }}
            >
              <span
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: radius.pill,
                  backgroundColor: colors.accentLight,
                  color: colors.accent,
                  fontSize: font.size.sm,
                  fontWeight: font.weight.bold,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {i + 1}
              </span>
              <span style={{ fontSize: font.size.md, color: colors.text1, lineHeight: 1.5 }}>{g}</span>
            </div>
          ))}
        </div>

        <button
          onClick={onClose}
          style={{
            width: '100%',
            padding: '15px',
            backgroundColor: colors.accent,
            color: '#fff',
            border: 'none',
            borderRadius: radius.xl,
            fontSize: font.size.md,
            fontWeight: font.weight.semibold,
            cursor: 'pointer',
          }}
        >
          확인
        </button>
      </div>
    </div>
  )
}
