import { useLocation, useNavigate } from 'react-router-dom'
import RiskBadge from '../components/RiskBadge'
import VisitBanner from '../components/VisitBanner'
import { colors, font, radius, shadow } from '../theme'
import { useEffect } from 'react'

interface Condition { label: string; score: number }

interface SkinMetrics {
  oiliness: number
  moisture: number
  trouble: number
  sensitivity: number
}

interface AnalysisResult {
  id: number
  analysis_type: string
  risk_level: string
  conditions: Condition[]
  confidence: number
  skin_metrics: SkinMetrics | null
  gemini_explanation: string | null
  recommend_visit: boolean
  visit_message: string | null
  is_diagnostic: boolean
  disclaimer: string
  created_at: string
  _fromType?: string  // Upload에서 전달된 분석 타입
}

const TYPE_KO: Record<string, string> = { skin: '안면피부', scalp: '두피', lesion: '병변' }

const scoreColor = (score: number) => {
  if (score >= 0.7) return colors.danger
  if (score >= 0.4) return colors.warning
  return colors.success
}

// 피부 지표 게이지 색상 (지표별 의미 반영)
const metricColor = (key: string, value: number) => {
  if (key === 'moisture') {
    // 수분은 높을수록 좋음
    if (value >= 60) return colors.success
    if (value >= 40) return colors.warning
    return colors.danger
  }
  // 유분·트러블·민감도는 낮을수록 좋음
  if (value <= 30) return colors.success
  if (value <= 60) return colors.warning
  return colors.danger
}

const METRIC_LABELS: Record<keyof SkinMetrics, string> = {
  oiliness: '유분도',
  moisture: '수분도',
  trouble: '트러블',
  sensitivity: '민감도',
}

export default function Result() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const result = state as AnalysisResult | null

  // 결과 페이지 진입 시 스크롤 최상단
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  // 새 분석: Upload로 이동 (state 없이 → location.key 변경으로 Upload 초기화)
  const handleNewAnalysis = () => {
    navigate('/', { replace: false })
  }

  // 같은 부위 재분석: 타입 유지하고 Upload로 이동
  const handleSameTypeAnalysis = () => {
    if (result?._fromType) {
      localStorage.setItem('last_analysis_type', result._fromType)
    }
    navigate('/', { replace: false })
  }

  if (!result) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <p style={{ color: colors.text2, marginBottom: 16 }}>결과 데이터가 없습니다.</p>
        <button
          onClick={() => navigate('/')}
          style={{ color: colors.accent, background: 'none', border: 'none', cursor: 'pointer', fontSize: font.size.md }}
        >
          홈으로
        </button>
      </div>
    )
  }

  return (
    <div style={{ padding: '20px 16px', backgroundColor: colors.bg }}>
      {/* 헤더 */}
      <h1
        style={{
          fontSize: font.size.xxl,
          fontWeight: font.weight.bold,
          color: colors.text1,
          letterSpacing: '-0.02em',
          marginBottom: 4,
        }}
      >
        {TYPE_KO[result.analysis_type] ?? result.analysis_type}
      </h1>
      <p style={{ fontSize: font.size.sm, color: colors.text2, marginBottom: 20 }}>
        {new Date(result.created_at).toLocaleString('ko-KR')}
      </p>

      {/* 위험도 + 신뢰도 카드 */}
      <div
        style={{
          backgroundColor: colors.card,
          borderRadius: radius.xl,
          padding: '16px 20px',
          marginBottom: 12,
          boxShadow: shadow.card,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <p style={{ fontSize: font.size.xs, color: colors.text2, marginBottom: 6, fontWeight: font.weight.medium, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            위험도
          </p>
          <RiskBadge level={result.risk_level} />
        </div>
        <div style={{ textAlign: 'right' }}>
          <p style={{ fontSize: font.size.xs, color: colors.text2, marginBottom: 4, fontWeight: font.weight.medium, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            신뢰도
          </p>
          <p style={{ fontSize: font.size.xl, fontWeight: font.weight.bold, color: colors.accent }}>
            {Math.round(result.confidence * 100)}%
          </p>
        </div>
      </div>

      {/* 병원 방문 배너 */}
      {result.recommend_visit && result.visit_message && (
        <div style={{ marginBottom: 12 }}>
          <VisitBanner message={result.visit_message} />
        </div>
      )}

      {/* 피부 지표 카드 */}
      {result.skin_metrics && (
        <div
          style={{
            backgroundColor: colors.card,
            borderRadius: radius.xl,
            padding: '16px 20px',
            marginBottom: 12,
            boxShadow: shadow.card,
          }}
        >
          <p
            style={{
              fontSize: font.size.xs,
              fontWeight: font.weight.semibold,
              color: colors.text2,
              marginBottom: 16,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            피부 지표
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 20px' }}>
            {(Object.keys(METRIC_LABELS) as (keyof SkinMetrics)[]).map((key) => {
              const value = result.skin_metrics![key]
              const color = metricColor(key, value)
              return (
                <div key={key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                    <span style={{ fontSize: font.size.sm, color: colors.text2 }}>
                      {METRIC_LABELS[key]}
                    </span>
                    <span style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color }}>
                      {value}
                    </span>
                  </div>
                  <div style={{ height: 6, backgroundColor: colors.bgSecondary, borderRadius: 3, overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${value}%`,
                        height: '100%',
                        backgroundColor: color,
                        borderRadius: 3,
                        transition: 'width 0.6s ease',
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 감지된 상태 */}
      <div
        style={{
          backgroundColor: colors.card,
          borderRadius: radius.xl,
          padding: '16px 20px',
          marginBottom: 12,
          boxShadow: shadow.card,
        }}
      >
        <p
          style={{
            fontSize: font.size.xs,
            fontWeight: font.weight.semibold,
            color: colors.text2,
            marginBottom: 14,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          감지된 상태
        </p>
        {result.conditions.map((c, i) => (
          <div
            key={c.label}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              paddingBottom: i < result.conditions.length - 1 ? 12 : 0,
              marginBottom: i < result.conditions.length - 1 ? 12 : 0,
              borderBottom: i < result.conditions.length - 1 ? `1px solid ${colors.divider}` : 'none',
            }}
          >
            <span style={{ fontSize: font.size.md, color: colors.text1 }}>{c.label}</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 90, height: 6, backgroundColor: colors.bgSecondary, borderRadius: 3, overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${c.score * 100}%`,
                    height: '100%',
                    backgroundColor: scoreColor(c.score),
                    borderRadius: 3,
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
              <span style={{ fontSize: font.size.sm, color: scoreColor(c.score), fontWeight: font.weight.semibold, minWidth: 34, textAlign: 'right' }}>
                {Math.round(c.score * 100)}%
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* AI 설명 */}
      {result.gemini_explanation && (
        <div
          style={{
            backgroundColor: colors.accentLight,
            borderRadius: radius.xl,
            padding: '16px 20px',
            marginBottom: 12,
          }}
        >
          <p
            style={{
              fontSize: font.size.xs,
              fontWeight: font.weight.semibold,
              color: colors.accent,
              marginBottom: 10,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            AI 분석 설명
          </p>
          <p style={{ fontSize: font.size.md, lineHeight: 1.7, color: colors.text1, whiteSpace: 'pre-wrap' }}>
            {result.gemini_explanation}
          </p>
        </div>
      )}

      {/* 면책 */}
      <p
        style={{
          fontSize: font.size.xs,
          color: colors.text3,
          lineHeight: 1.5,
          padding: '12px 4px',
          borderTop: `1px solid ${colors.divider}`,
          marginBottom: 20,
        }}
      >
        ⚠️ {result.disclaimer}
      </p>

      {/* 재사용 버튼 영역 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 8 }}>

        {/* 같은 부위 재분석 — 가장 강조 */}
        <button
          onClick={handleSameTypeAnalysis}
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
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
          }}
        >
          <span>🔄</span>
          {TYPE_KO[result.analysis_type] ?? result.analysis_type} 재분석
        </button>

        <div style={{ display: 'flex', gap: 10 }}>
          {/* 다른 부위 새 분석 */}
          <button
            onClick={handleNewAnalysis}
            style={{
              flex: 1,
              padding: '13px',
              backgroundColor: colors.bgSecondary,
              color: colors.text1,
              border: 'none',
              borderRadius: radius.xl,
              fontSize: font.size.sm,
              fontWeight: font.weight.semibold,
              cursor: 'pointer',
            }}
          >
            다른 부위 분석
          </button>

          {/* 기록 보기 */}
          <button
            onClick={() => navigate('/records')}
            style={{
              flex: 1,
              padding: '13px',
              backgroundColor: colors.card,
              color: colors.text1,
              border: `1.5px solid ${colors.divider}`,
              borderRadius: radius.xl,
              fontSize: font.size.sm,
              fontWeight: font.weight.semibold,
              cursor: 'pointer',
            }}
          >
            내 기록
          </button>
        </div>
      </div>
    </div>
  )
}
