import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getLesionTrackHistory } from '../api/client'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { colors, font, radius, shadow } from '../theme'

interface LesionEntry {
  id: number
  risk_level: string | null
  asymmetry_score: number | null
  border_score: number | null
  color_variance: number | null
  size_mm: number | null
  created_at: string
}

const RISK_NUM: Record<string, number> = { normal: 0, mild: 1, suspicious: 2, danger: 3 }

export default function Compare() {
  const { trackId } = useParams<{ trackId: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<LesionEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!trackId) return
    getLesionTrackHistory(Number(trackId))
      .then((res) => setData(res.data))
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }, [trackId])

  const chartData = data.map((d) => ({
    date: new Date(d.created_at).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
    위험도: RISK_NUM[d.risk_level ?? 'normal'] ?? 0,
    비대칭: d.asymmetry_score ?? 0,
    경계: d.border_score ?? 0,
    크기: d.size_mm ?? 0,
  }))

  return (
    <div style={{ padding: '20px 16px', backgroundColor: colors.bg, minHeight: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <button
          onClick={() => navigate(-1)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: colors.accent, fontSize: font.size.body, padding: 0 }}
        >
          ‹
        </button>
        <h1
          style={{
            fontSize: font.size.xl,
            fontWeight: font.weight.bold,
            color: colors.text1,
            letterSpacing: '-0.02em',
          }}
        >
          병변 변화 추적
        </h1>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: colors.text2 }}>
          불러오는 중...
        </div>
      ) : data.length < 2 ? (
        <div
          style={{
            backgroundColor: colors.card,
            borderRadius: radius.xl,
            padding: '32px 20px',
            boxShadow: shadow.card,
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 36, marginBottom: 12 }}>📈</div>
          <p style={{ color: colors.text2, fontSize: font.size.md }}>
            비교하려면 같은 트랙에 2회 이상 분석이 필요합니다.
          </p>
        </div>
      ) : (
        <>
          <div
            style={{
              backgroundColor: colors.card,
              borderRadius: radius.xl,
              padding: '20px 16px',
              boxShadow: shadow.card,
              marginBottom: 16,
            }}
          >
            <p style={{ fontSize: font.size.xs, fontWeight: font.weight.semibold, color: colors.text2, marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              지표 변화
            </p>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.divider} />
                <XAxis dataKey="date" fontSize={11} tick={{ fill: colors.text2 }} />
                <YAxis fontSize={11} tick={{ fill: colors.text2 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: colors.card,
                    border: `1px solid ${colors.border}`,
                    borderRadius: radius.md,
                    fontSize: font.size.sm,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: font.size.sm }} />
                <Line type="monotone" dataKey="위험도" stroke={colors.danger} strokeWidth={2} dot={{ fill: colors.danger, r: 4 }} />
                <Line type="monotone" dataKey="비대칭" stroke={colors.warning} strokeWidth={2} dot={{ fill: colors.warning, r: 4 }} />
                <Line type="monotone" dataKey="경계" stroke="#8e24aa" strokeWidth={2} dot={{ fill: '#8e24aa', r: 4 }} />
                <Line type="monotone" dataKey="크기" stroke={colors.accent} strokeWidth={2} dot={{ fill: colors.accent, r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* 데이터 요약 */}
          <div
            style={{
              backgroundColor: colors.card,
              borderRadius: radius.xl,
              boxShadow: shadow.card,
              overflow: 'hidden',
            }}
          >
            {data.map((d, i) => (
              <div
                key={d.id}
                style={{
                  padding: '12px 16px',
                  borderBottom: i < data.length - 1 ? `1px solid ${colors.divider}` : 'none',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <p style={{ fontSize: font.size.sm, color: colors.text2 }}>
                  {new Date(d.created_at).toLocaleDateString('ko-KR')}
                </p>
                <p style={{ fontSize: font.size.sm, color: colors.text1, fontWeight: font.weight.medium }}>
                  {d.risk_level ?? '-'}
                </p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
