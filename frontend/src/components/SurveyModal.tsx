import { useState } from 'react'
import { colors, font, radius, shadow } from '../theme'

export interface SurveyData {
  bodyPart: string
  smoking: boolean | null
  drinking: boolean | null
  symptomDescription: string
}

const BODY_PARTS = ['얼굴', '팔', '다리', '등', '가슴', '배']

interface Props {
  analysisType?: 'skin' | 'lesion'
  onConfirm: (data: SurveyData) => void
  onClose: () => void
}

export default function SurveyModal({ analysisType = 'skin', onConfirm, onClose }: Props) {
  const [bodyPart, setBodyPart] = useState('')
  const [smoking, setSmoking] = useState<boolean | null>(null)
  const [drinking, setDrinking] = useState<boolean | null>(null)
  const [symptomDescription, setSymptomDescription] = useState('')

  const canConfirm = bodyPart !== '' && smoking !== null && drinking !== null
  const showSymptomDescription = analysisType === 'skin'

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        zIndex: 2000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: colors.card,
          borderRadius: `${radius.xl}px ${radius.xl}px 0 0`,
          padding: '8px 20px 36px',
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

        <h3 style={{ fontSize: font.size.lg, fontWeight: font.weight.bold, color: colors.text1, marginBottom: 4 }}>
          분석 전 설문
        </h3>
        <p style={{ fontSize: font.size.sm, color: colors.text2, marginBottom: 20 }}>
          정확한 분석을 위해 간단한 정보를 입력해 주세요
        </p>

        {/* 부위 선택 */}
        <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, marginBottom: 10 }}>
          분석 부위
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 20 }}>
          {BODY_PARTS.map((part) => (
            <button
              key={part}
              onClick={() => setBodyPart(part)}
              style={{
                padding: '10px 6px',
                borderRadius: radius.md,
                border: `1.5px solid ${bodyPart === part ? colors.accent : colors.border}`,
                backgroundColor: bodyPart === part ? colors.accentLight : colors.bg,
                color: bodyPart === part ? colors.accent : colors.text2,
                fontSize: font.size.sm,
                fontWeight: bodyPart === part ? font.weight.semibold : font.weight.regular,
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {part}
            </button>
          ))}
        </div>

        {showSymptomDescription && (
          <div style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 10 }}>
              <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, margin: 0 }}>
                증상 설명
              </p>
              <span style={{ fontSize: font.size.xs, color: colors.text3 }}>
                선택 입력
              </span>
            </div>
            <textarea
              value={symptomDescription}
              onChange={(e) => setSymptomDescription(e.target.value.slice(0, 500))}
              placeholder="예: 최근 볼 주변이 붉고 따가워요. 세안 후 건조함이 심하고 트러블이 늘었어요."
              rows={3}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                resize: 'none',
                padding: '12px 14px',
                borderRadius: radius.md,
                border: `1.5px solid ${symptomDescription.trim() ? colors.accent : colors.border}`,
                backgroundColor: symptomDescription.trim() ? colors.accentLight : colors.bg,
                color: colors.text1,
                fontSize: font.size.sm,
                lineHeight: 1.45,
                outline: 'none',
              }}
            />
            <p style={{ marginTop: 6, marginBottom: 0, fontSize: font.size.xs, color: colors.text3, textAlign: 'right' }}>
              {symptomDescription.length}/500
            </p>
          </div>
        )}

        {/* 흡연 여부 */}
        <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, marginBottom: 10 }}>
          흡연 여부
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 20 }}>
          {[{ label: '흡연', value: true }, { label: '비흡연', value: false }].map((opt) => (
            <button
              key={String(opt.value)}
              onClick={() => setSmoking(opt.value)}
              style={{
                padding: '10px',
                borderRadius: radius.md,
                border: `1.5px solid ${smoking === opt.value ? colors.accent : colors.border}`,
                backgroundColor: smoking === opt.value ? colors.accentLight : colors.bg,
                color: smoking === opt.value ? colors.accent : colors.text2,
                fontSize: font.size.sm,
                fontWeight: smoking === opt.value ? font.weight.semibold : font.weight.regular,
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* 음주 여부 */}
        <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, marginBottom: 10 }}>
          음주 여부
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 24 }}>
          {[{ label: '음주', value: true }, { label: '비음주', value: false }].map((opt) => (
            <button
              key={String(opt.value)}
              onClick={() => setDrinking(opt.value)}
              style={{
                padding: '10px',
                borderRadius: radius.md,
                border: `1.5px solid ${drinking === opt.value ? colors.accent : colors.border}`,
                backgroundColor: drinking === opt.value ? colors.accentLight : colors.bg,
                color: drinking === opt.value ? colors.accent : colors.text2,
                fontSize: font.size.sm,
                fontWeight: drinking === opt.value ? font.weight.semibold : font.weight.regular,
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* 확인 버튼 */}
        <button
          onClick={() => canConfirm && onConfirm({
            bodyPart,
            smoking: smoking!,
            drinking: drinking!,
            symptomDescription: symptomDescription.trim(),
          })}
          disabled={!canConfirm}
          style={{
            width: '100%',
            padding: '15px',
            borderRadius: radius.xl,
            border: 'none',
            backgroundColor: canConfirm ? colors.accent : colors.bgSecondary,
            color: canConfirm ? '#fff' : colors.text3,
            fontSize: font.size.md,
            fontWeight: font.weight.semibold,
            cursor: canConfirm ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s',
          }}
        >
          {canConfirm ? '사진 선택하기' : '모든 항목을 선택해 주세요'}
        </button>
      </div>
    </div>
  )
}
