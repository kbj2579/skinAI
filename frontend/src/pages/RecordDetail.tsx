import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getRecord } from '../api/client'
import RiskBadge from '../components/RiskBadge'
import VisitBanner from '../components/VisitBanner'
import { SkeletonDetailCard } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'
import { colors, font, radius, shadow } from '../theme'

interface ConditionItem { label: string; score: number }
interface SkinMetrics { oiliness: number; moisture: number; trouble: number; sensitivity: number }

interface RecordDetail {
  id: number
  analysis_type: string
  risk_level: string
  conditions: ConditionItem[] | null
  confidence: number | null
  skin_metrics: SkinMetrics | null
  gemini_explanation: string | null
  recommend_visit: boolean
  is_diagnostic: boolean
  disclaimer: string
  created_at: string
}

const TYPE_LABELS: Record<string, string> = { skin: '안면피부', scalp: '두피', lesion: '병변' }

const METRIC_LABELS: Record<keyof SkinMetrics, string> = {
  oiliness: '유분도', moisture: '수분도', trouble: '트러블', sensitivity: '민감도',
}

const scoreColor = (score: number) => {
  if (score >= 0.7) return colors.danger
  if (score >= 0.4) return colors.warning
  return colors.success
}

const metricColor = (key: string, value: number) => {
  if (key === 'moisture') {
    if (value >= 60) return colors.success
    if (value >= 40) return colors.warning
    return colors.danger
  }
  if (value <= 30) return colors.success
  if (value <= 60) return colors.warning
  return colors.danger
}

export default function RecordDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [record, setRecord] = useState<RecordDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const { show } = useToast()

  useEffect(() => {
    if (!id) return
    getRecord(Number(id))
      .then((res) => setRecord(res.data))
      .catch((err: any) => {
        show(err.message ?? '기록을 불러올 수 없습니다.', 'error')
        navigate('/records', { replace: true })
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <SkeletonDetailCard />
  if (!record) return null

  const handleReanalyze = () => {
    localStorage.setItem('last_analysis_type', record.analysis_type)
    navigate('/')
  }

  return (
    <div style={{ padding: '20px 16px 100px', backgroundColor: colors.bg }}>
      {/* 헤더 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
        <button
          onClick={() => navigate('/records')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: colors.accent, fontSize: font.size.body, padding: 0 }}
        >
          ‹
        </button>
        <h1 style={{ fontSize: font.size.xl, fontWeight: font.weight.bold, color: colors.text1, letterSpacing: '-0.02em', flex: 1 }}>
          {TYPE_LABELS[record.analysis_type] ?? record.analysis_type}
        </h1>
        <RiskBadge level={record.risk_level} />
      </div>
      <p style={{ fontSize: font.size.xs, color: colors.text2, marginBottom: 20, paddingLeft: 32 }}>
        {new Date(record.created_at).toLocaleString('ko-KR')}
      </p>

      {/* 병원 방문 배너 */}
      {record.recommend_visit && (
        <div style={{ marginBottom: 12 }}>
          <VisitBanner message="전문의 진료가 권장됩니다. 가까운 피부과를 방문하세요." />
        </div>
      )}

      {/* 신뢰도 */}
      {record.confidence != null && (
        <div
          style={{
            backgroundColor: colors.card, borderRadius: radius.xl, padding: '14px 20px',
            marginBottom: 12, boxShadow: shadow.card,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}
        >
          <span style={{ fontSize: font.size.md, color: colors.text2 }}>분석 신뢰도</span>
          <span style={{ fontSize: font.size.xl, fontWeight: font.weight.bold, color: colors.accent }}>
            {(record.confidence * 100).toFixed(1)}%
          </span>
        </div>
      )}

      {/* 피부 지표 — DB에 저장된 경우 표시 */}
      {record.skin_metrics && (
        <div style={{ backgroundColor: colors.card, borderRadius: radius.xl, padding: '16px 20px', marginBottom: 12, boxShadow: shadow.card }}>
          <p style={{ fontSize: font.size.xs, fontWeight: font.weight.semibold, color: colors.text2, marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            피부 지표
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 20px' }}>
            {(Object.keys(METRIC_LABELS) as (keyof SkinMetrics)[]).map((key) => {
              const value = record.skin_metrics![key]
              const color = metricColor(key, value)
              return (
                <div key={key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                    <span style={{ fontSize: font.size.sm, color: colors.text2 }}>{METRIC_LABELS[key]}</span>
                    <span style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color }}>{value}</span>
                  </div>
                  <div style={{ height: 6, backgroundColor: colors.bgSecondary, borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${value}%`, height: '100%', backgroundColor: color, borderRadius: 3, transition: 'width 0.6s ease' }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 감지된 상태 */}
      {record.conditions && record.conditions.length > 0 && (
        <div style={{ backgroundColor: colors.card, borderRadius: radius.xl, padding: '16px 20px', marginBottom: 12, boxShadow: shadow.card }}>
          <p style={{ fontSize: font.size.xs, fontWeight: font.weight.semibold, color: colors.text2, marginBottom: 14, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            감지된 상태
          </p>
          {record.conditions.map((c, i) => (
            <div
              key={i}
              style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                paddingBottom: i < record.conditions!.length - 1 ? 12 : 0,
                marginBottom: i < record.conditions!.length - 1 ? 12 : 0,
                borderBottom: i < record.conditions!.length - 1 ? `1px solid ${colors.divider}` : 'none',
              }}
            >
              <span style={{ fontSize: font.size.md, color: colors.text1 }}>{c.label}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 80, height: 6, backgroundColor: colors.bgSecondary, borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: `${c.score * 100}%`, height: '100%', backgroundColor: scoreColor(c.score), borderRadius: 3 }} />
                </div>
                <span style={{ fontSize: font.size.sm, color: scoreColor(c.score), fontWeight: font.weight.semibold, minWidth: 34, textAlign: 'right' }}>
                  {(c.score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AI 설명 */}
      {record.gemini_explanation && (
        <div style={{ backgroundColor: colors.accentLight, borderRadius: radius.xl, padding: '16px 20px', marginBottom: 12 }}>
          <p style={{ fontSize: font.size.xs, fontWeight: font.weight.semibold, color: colors.accent, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            AI 분석 설명
          </p>
          <p style={{ fontSize: font.size.md, lineHeight: 1.7, color: colors.text1, whiteSpace: 'pre-line' }}>
            {record.gemini_explanation}
          </p>
        </div>
      )}

      {/* 면책 */}
      <p style={{ fontSize: font.size.xs, color: colors.text3, lineHeight: 1.5, borderTop: `1px solid ${colors.divider}`, paddingTop: 12, marginBottom: 20 }}>
        {record.disclaimer}
      </p>

      {/* 재분석 버튼 */}
      <button
        onClick={handleReanalyze}
        style={{
          width: '100%', padding: '14px',
          backgroundColor: colors.accent, color: '#fff',
          border: 'none', borderRadius: radius.xl,
          fontSize: font.size.md, fontWeight: font.weight.semibold,
          cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
        }}
      >
        <span>🔄</span>
        {TYPE_LABELS[record.analysis_type] ?? record.analysis_type} 재분석
      </button>
    </div>
  )
}
