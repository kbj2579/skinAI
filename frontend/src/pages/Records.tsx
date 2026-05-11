import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { listRecords, AnalysisType } from '../api/client'
import RiskBadge from '../components/RiskBadge'
import { SkeletonRecordList } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'
import { colors, font, radius, shadow } from '../theme'

interface RecordSummary {
  id: number
  analysis_type: string
  risk_level: string
  confidence: number | null
  recommend_visit: boolean
  created_at: string
}

const TYPE_LABELS: Record<string, string> = { skin: '안면피부', scalp: '두피', lesion: '병변' }
const FILTER_OPTIONS: (AnalysisType | undefined)[] = [undefined, 'skin', 'scalp', 'lesion']
const PAGE_SIZE = 10

export default function Records() {
  const [records, setRecords] = useState<RecordSummary[]>([])
  const [total, setTotal] = useState(0)
  const [filter, setFilter] = useState<AnalysisType | undefined>()
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [offset, setOffset] = useState(0)
  const navigate = useNavigate()
  const { show } = useToast()

  const fetchRecords = useCallback(async (f: AnalysisType | undefined, reset: boolean) => {
    if (reset) setLoading(true)
    try {
      const res = await listRecords(f, PAGE_SIZE, reset ? 0 : offset)
      const data = res.data
      const items: RecordSummary[] = Array.isArray(data) ? data : (data.items ?? [])
      const tot: number = Array.isArray(data) ? data.length : (data.total ?? 0)
      if (reset) {
        setRecords(items)
        setOffset(items.length)
      } else {
        setRecords((prev) => [...prev, ...items])
        setOffset((prev) => prev + items.length)
      }
      setTotal(tot)
    } catch (err: any) {
      show(err.message ?? '기록을 불러오지 못했습니다.', 'error')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [offset, show])

  useEffect(() => {
    setOffset(0)
    fetchRecords(filter, true)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter])

  const handleLoadMore = async () => {
    setLoadingMore(true)
    await fetchRecords(filter, false)
  }

  const hasMore = records.length < total

  return (
    <div style={{ padding: '20px 16px 100px', backgroundColor: colors.bg, minHeight: '100%' }}>
      {/* 헤더 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 4 }}>
        <h1 style={{ fontSize: font.size.xxl, fontWeight: font.weight.bold, color: colors.text1, letterSpacing: '-0.02em' }}>
          분석 기록
        </h1>
        {!loading && total > 0 && (
          <span
            style={{
              fontSize: font.size.sm,
              color: colors.accent,
              fontWeight: font.weight.semibold,
              backgroundColor: colors.accentLight,
              padding: '3px 10px',
              borderRadius: radius.pill,
            }}
          >
            총 {total}건
          </span>
        )}
      </div>
      <p style={{ fontSize: font.size.sm, color: colors.text2, marginBottom: 20 }}>
        {loading ? ' ' : total === 0 ? '아직 분석 기록이 없습니다' : `${records.length}건 표시 중`}
      </p>

      {/* 필터 */}
      <div
        style={{
          display: 'flex',
          backgroundColor: colors.bgSecondary,
          borderRadius: radius.lg,
          padding: 3,
          marginBottom: 20,
        }}
      >
        {FILTER_OPTIONS.map((t) => (
          <button
            key={t ?? 'all'}
            onClick={() => { if (!loading) setFilter(t) }}
            style={{
              flex: 1,
              padding: '8px 4px',
              borderRadius: radius.md,
              border: 'none',
              fontSize: font.size.sm,
              fontWeight: font.weight.semibold,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.2s',
              backgroundColor: filter === t ? colors.card : 'transparent',
              color: filter === t ? colors.text1 : colors.text2,
              boxShadow: filter === t ? shadow.card : 'none',
            }}
          >
            {t ? TYPE_LABELS[t] : '전체'}
          </button>
        ))}
      </div>

      {/* 리스트 */}
      {loading ? (
        <SkeletonRecordList count={6} />
      ) : records.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>📋</div>
          <p style={{ color: colors.text2, fontSize: font.size.md, marginBottom: 20 }}>
            {filter ? `${TYPE_LABELS[filter]} 분석 기록이 없습니다` : '분석 기록이 없습니다'}
          </p>
          <button
            onClick={() => navigate('/')}
            style={{
              padding: '12px 28px',
              backgroundColor: colors.accent,
              color: '#fff',
              border: 'none',
              borderRadius: radius.xl,
              fontSize: font.size.md,
              fontWeight: font.weight.semibold,
              cursor: 'pointer',
            }}
          >
            첫 분석 시작하기
          </button>
        </div>
      ) : (
        <>
          <div
            style={{
              backgroundColor: colors.card,
              borderRadius: radius.xl,
              boxShadow: shadow.card,
              overflow: 'hidden',
              marginBottom: hasMore ? 12 : 0,
            }}
          >
            {records.map((r, i) => (
              <div
                key={r.id}
                onClick={() => navigate(`/records/${r.id}`)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === 'Enter') navigate(`/records/${r.id}`) }}
                style={{
                  padding: '14px 16px',
                  borderBottom: i < records.length - 1 ? `1px solid ${colors.divider}` : 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'background-color 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = colors.bgSecondary)}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: font.size.md, fontWeight: font.weight.medium, color: colors.text1, marginBottom: 3 }}>
                    {TYPE_LABELS[r.analysis_type] ?? r.analysis_type} 분석
                    {r.recommend_visit && <span style={{ marginLeft: 6, fontSize: font.size.xs, color: colors.warning }}>🏥 방문권장</span>}
                  </p>
                  <p style={{ fontSize: font.size.xs, color: colors.text2 }}>
                    {new Date(r.created_at).toLocaleString('ko-KR', {
                      year: 'numeric', month: 'short', day: 'numeric',
                      hour: '2-digit', minute: '2-digit',
                    })}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                  <RiskBadge level={r.risk_level} />
                  <span style={{ color: colors.text3, fontSize: 20, fontWeight: 300 }}>›</span>
                </div>
              </div>
            ))}
          </div>

          {/* Load More 버튼 */}
          {hasMore && (
            <button
              onClick={handleLoadMore}
              disabled={loadingMore}
              style={{
                width: '100%',
                padding: '13px',
                backgroundColor: colors.card,
                color: loadingMore ? colors.text3 : colors.accent,
                border: `1.5px solid ${colors.divider}`,
                borderRadius: radius.xl,
                fontSize: font.size.sm,
                fontWeight: font.weight.semibold,
                cursor: loadingMore ? 'not-allowed' : 'pointer',
                boxShadow: shadow.card,
                transition: 'all 0.2s',
              }}
            >
              {loadingMore ? '불러오는 중...' : `더 보기 (${total - records.length}건 남음)`}
            </button>
          )}
        </>
      )}
    </div>
  )
}
