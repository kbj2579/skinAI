import { useEffect, useRef, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { analyze, AnalysisType, listLesionTracks, createLesionTrack, listRecords } from '../api/client'
import ImageGuide from '../components/ImageGuide'
import { useToast } from '../context/ToastContext'
import { colors, font, radius, shadow } from '../theme'

const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif']

const TYPE_LABELS: Record<AnalysisType, string> = {
  skin: '안면피부',
  scalp: '두피',
  lesion: '병변',
}

// 로딩 단계
const LOADING_STEPS = [
  { icon: '🗜️', label: '이미지 최적화 중...' },
  { icon: '📡', label: '서버 전송 중...' },
  { icon: '🤖', label: 'AI 분석 중...' },
]

function resizeImage(file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      const canvas = document.createElement('canvas')
      canvas.width = 1024
      canvas.height = 1024
      const ctx = canvas.getContext('2d')!
      ctx.drawImage(img, 0, 0, 1024, 1024)
      canvas.toBlob(
        (blob) => { if (blob) resolve(blob); else reject(new Error('이미지 변환 실패')) },
        'image/jpeg', 0.85,
      )
    }
    img.onerror = reject
    img.src = url
  })
}

interface LesionTrack { id: number; track_name: string | null }

export default function Upload() {
  // location.key가 바뀔 때마다 컴포넌트가 새로 렌더링됨
  const location = useLocation()
  const navigate = useNavigate()

  // 마지막 선택 타입 복원 (localStorage)
  const savedType = (localStorage.getItem('last_analysis_type') as AnalysisType) ?? 'skin'
  const [type, setType] = useState<AnalysisType>(savedType)
  const [preview, setPreview] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [showGuide, setShowGuide] = useState(false)
  const [error, setError] = useState('')
  const [totalCount, setTotalCount] = useState<number | null>(null)

  const cameraRef = useRef<HTMLInputElement>(null)
  const galleryRef = useRef<HTMLInputElement>(null)

  const [tracks, setTracks] = useState<LesionTrack[]>([])
  const [selectedTrackId, setSelectedTrackId] = useState<number | undefined>()
  const [newTrackName, setNewTrackName] = useState('')
  const [creatingTrack, setCreatingTrack] = useState(false)
  const { show } = useToast()

  // 페이지 진입 시 상태 초기화 (result에서 돌아올 때 깨끗하게)
  useEffect(() => {
    setPreview(null)
    setFile(null)
    setError('')
    setLoadingStep(0)
  }, [location.key])

  // 분석 유형 변경 시 저장 + 병변 트랙 로드
  useEffect(() => {
    localStorage.setItem('last_analysis_type', type)
    if (type === 'lesion') {
      listLesionTracks().then((res) => setTracks(res.data)).catch(() => setTracks([]))
    }
  }, [type])

  // 누적 분석 횟수 로드
  useEffect(() => {
    listRecords(undefined, 1, 0)
      .then((res) => {
        const data = res.data
        // { total, items } 구조
        if (typeof data?.total === 'number') setTotalCount(data.total)
        else if (Array.isArray(data)) setTotalCount(data.length)
      })
      .catch(() => {})
  }, [location.key])

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    e.target.value = ''

    // 파일 크기 검증
    if (f.size > MAX_FILE_SIZE) {
      show('파일 크기는 20MB를 초과할 수 없습니다.', 'error')
      return
    }
    // 파일 타입 검증
    if (!ALLOWED_TYPES.includes(f.type) && !f.type.startsWith('image/')) {
      show('JPG, PNG, WebP 이미지 파일만 업로드할 수 있습니다.', 'error')
      return
    }

    setFile(f)
    setPreview(URL.createObjectURL(f))
    setError('')
    show('사진이 선택됐습니다.', 'success')
  }

  const handleReset = () => {
    setFile(null)
    setPreview(null)
    setError('')
  }

  const handleCreateTrack = async () => {
    if (!newTrackName.trim()) return
    setCreatingTrack(true)
    try {
      const res = await createLesionTrack(newTrackName.trim())
      setTracks((prev) => [...prev, res.data])
      setSelectedTrackId(res.data.id)
      setNewTrackName('')
      show('트랙이 생성됐습니다.', 'success')
    } catch (err: any) {
      show(err.message ?? '트랙 생성에 실패했습니다.', 'error')
    } finally {
      setCreatingTrack(false)
    }
  }

  const handleSubmit = async () => {
    if (!file) { setError('사진을 먼저 선택해 주세요.'); return }
    setLoading(true)
    setError('')

    // 단계 1: 이미지 최적화
    setLoadingStep(0)
    let resized: Blob
    try {
      resized = await resizeImage(file)
    } catch {
      setError('이미지 처리에 실패했습니다. 다른 사진을 선택해 주세요.')
      setLoading(false)
      return
    }

    // 단계 2: 서버 전송
    setLoadingStep(1)
    await new Promise((r) => setTimeout(r, 300)) // 단계 전환 표시

    try {
      // 단계 3: AI 분석 (실제 API 호출)
      setLoadingStep(2)
      const res = await analyze(type, resized, type === 'lesion' ? selectedTrackId : undefined)
      navigate('/result', { state: { ...res.data, _fromType: type } })
    } catch (err: any) {
      const msg = err.message ?? '분석 중 오류가 발생했습니다. 다시 시도해 주세요.'
      setError(msg)
      show(msg, 'error')
      setLoading(false)
    }
  }

  // ── 로딩 오버레이 ───────────────────────────────────────────────
  if (loading) {
    return (
      <div
        style={{
          padding: '0 24px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 500,
          backgroundColor: colors.bg,
        }}
      >
        {/* 미리보기 축소 */}
        {preview && (
          <img
            src={preview}
            alt="분석 중"
            style={{
              width: 120,
              height: 120,
              borderRadius: radius.xl,
              objectFit: 'cover',
              marginBottom: 28,
              boxShadow: shadow.strong,
              opacity: 0.7,
            }}
          />
        )}

        {/* 스피너 */}
        <div
          style={{
            width: 52,
            height: 52,
            borderRadius: '50%',
            border: `3px solid ${colors.bgSecondary}`,
            borderTop: `3px solid ${colors.accent}`,
            animation: 'spin 0.8s linear infinite',
            marginBottom: 24,
          }}
        />

        {/* 단계 표시 */}
        <div style={{ width: '100%', maxWidth: 260 }}>
          {LOADING_STEPS.map((step, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 0',
                opacity: i < loadingStep ? 0.35 : i === loadingStep ? 1 : 0.3,
                transition: 'opacity 0.4s',
              }}
            >
              <span style={{ fontSize: 18 }}>{step.icon}</span>
              <span
                style={{
                  fontSize: font.size.sm,
                  color: i === loadingStep ? colors.text1 : colors.text2,
                  fontWeight: i === loadingStep ? font.weight.semibold : font.weight.regular,
                }}
              >
                {step.label}
              </span>
              {i < loadingStep && (
                <span style={{ marginLeft: 'auto', color: colors.success, fontSize: 14 }}>✓</span>
              )}
              {i === loadingStep && (
                <div
                  style={{
                    marginLeft: 'auto',
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: colors.accent,
                    animation: 'pulse 1s ease-in-out infinite',
                  }}
                />
              )}
            </div>
          ))}
        </div>

        <style>{`
          @keyframes spin { to { transform: rotate(360deg); } }
          @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
        `}</style>
      </div>
    )
  }

  // ── 메인 UI ─────────────────────────────────────────────────────
  return (
    <div style={{ padding: '20px 16px', backgroundColor: colors.bg, minHeight: '100%' }}>

      {/* 헤더 + 통계 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <h1
            style={{
              fontSize: font.size.xxl,
              fontWeight: font.weight.bold,
              color: colors.text1,
              letterSpacing: '-0.02em',
              marginBottom: 4,
            }}
          >
            피부 분석
          </h1>
          <p style={{ fontSize: font.size.sm, color: colors.text2 }}>
            부위를 선택하고 사진을 촬영하세요
          </p>
        </div>
        {totalCount !== null && (
          <div
            style={{
              backgroundColor: colors.accentLight,
              borderRadius: radius.lg,
              padding: '6px 12px',
              textAlign: 'center',
            }}
          >
            <p style={{ fontSize: font.size.xs, color: colors.accent, fontWeight: font.weight.semibold }}>
              누적 분석
            </p>
            <p style={{ fontSize: font.size.lg, fontWeight: font.weight.bold, color: colors.accent }}>
              {totalCount}회
            </p>
          </div>
        )}
      </div>

      {/* Segmented Control */}
      <div
        style={{
          display: 'flex',
          backgroundColor: colors.bgSecondary,
          borderRadius: radius.lg,
          padding: 3,
          marginBottom: 20,
        }}
      >
        {(Object.keys(TYPE_LABELS) as AnalysisType[]).map((t) => (
          <button
            key={t}
            onClick={() => { setType(t); setError('') }}
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
              backgroundColor: type === t ? colors.card : 'transparent',
              color: type === t ? colors.text1 : colors.text2,
              boxShadow: type === t ? shadow.card : 'none',
            }}
          >
            {TYPE_LABELS[t]}
          </button>
        ))}
      </div>

      {/* 병변 트랙 */}
      {type === 'lesion' && (
        <div
          style={{
            backgroundColor: colors.card,
            borderRadius: radius.lg,
            padding: 16,
            marginBottom: 16,
            boxShadow: shadow.card,
          }}
        >
          <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, marginBottom: 10 }}>
            병변 추적 트랙
          </p>
          <select
            value={selectedTrackId ?? ''}
            onChange={(e) => setSelectedTrackId(e.target.value ? Number(e.target.value) : undefined)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: radius.md,
              border: 'none',
              backgroundColor: colors.bg,
              fontSize: font.size.sm,
              color: colors.text1,
              marginBottom: 10,
              outline: 'none',
            }}
          >
            <option value="">트랙 없이 분석</option>
            {tracks.map((t) => (
              <option key={t.id} value={t.id}>{t.track_name ?? `트랙 #${t.id}`}</option>
            ))}
          </select>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              placeholder="새 트랙 이름"
              value={newTrackName}
              onChange={(e) => setNewTrackName(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleCreateTrack() }}
              style={{
                flex: 1,
                padding: '10px 12px',
                borderRadius: radius.md,
                border: 'none',
                backgroundColor: colors.bg,
                fontSize: font.size.sm,
                outline: 'none',
              }}
            />
            <button
              onClick={handleCreateTrack}
              disabled={creatingTrack || !newTrackName.trim()}
              style={{
                padding: '10px 16px',
                borderRadius: radius.md,
                border: 'none',
                backgroundColor: colors.accent,
                color: '#fff',
                fontSize: font.size.sm,
                fontWeight: font.weight.semibold,
                cursor: 'pointer',
                opacity: (!newTrackName.trim() || creatingTrack) ? 0.5 : 1,
              }}
            >
              추가
            </button>
          </div>
          {selectedTrackId != null && (
            <button
              onClick={() => navigate(`/compare/${selectedTrackId}`)}
              style={{
                width: '100%',
                marginTop: 10,
                padding: '10px 12px',
                borderRadius: radius.md,
                border: `1px solid ${colors.divider}`,
                backgroundColor: colors.bg,
                color: colors.text1,
                fontSize: font.size.sm,
                fontWeight: font.weight.semibold,
                cursor: 'pointer',
              }}
            >
              선택한 트랙 비교 보기
            </button>
          )}
        </div>
      )}

      {/* 이미지 영역 */}
      {preview ? (
        // 미리보기 + 교체 버튼
        <div style={{ position: 'relative', marginBottom: 16 }}>
          <img
            src={preview}
            alt="preview"
            style={{
              width: '100%',
              height: 240,
              objectFit: 'cover',
              borderRadius: radius.xl,
              boxShadow: shadow.card,
              display: 'block',
            }}
          />
          {/* 교체 버튼 */}
          <button
            onClick={handleReset}
            style={{
              position: 'absolute',
              top: 10,
              right: 10,
              backgroundColor: 'rgba(0,0,0,0.55)',
              color: '#fff',
              border: 'none',
              borderRadius: radius.pill,
              padding: '5px 12px',
              fontSize: font.size.xs,
              fontWeight: font.weight.semibold,
              cursor: 'pointer',
              backdropFilter: 'blur(6px)',
            }}
          >
            × 다시 선택
          </button>
        </div>
      ) : (
        // 카메라 / 갤러리 선택
        <div style={{ marginBottom: 16 }}>
          {/* 촬영 가이드 */}
          <button
            onClick={() => setShowGuide(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: font.size.sm,
              color: colors.accent,
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              marginBottom: 10,
              fontWeight: font.weight.medium,
            }}
          >
            <span>📷</span>
            촬영 가이드 보기
          </button>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {/* 카메라 직접 촬영 */}
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                backgroundColor: colors.accent,
                borderRadius: radius.xl,
                padding: '24px 16px',
                cursor: 'pointer',
                boxShadow: shadow.card,
              }}
            >
              <span style={{ fontSize: 32 }}>📷</span>
              <span style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: '#fff' }}>
                카메라 촬영
              </span>
              <input
                ref={cameraRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleFile}
                style={{ display: 'none' }}
              />
            </label>

            {/* 갤러리 선택 */}
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                backgroundColor: colors.card,
                border: `1.5px solid ${colors.border}`,
                borderRadius: radius.xl,
                padding: '24px 16px',
                cursor: 'pointer',
                boxShadow: shadow.card,
              }}
            >
              <span style={{ fontSize: 32 }}>🖼️</span>
              <span style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1 }}>
                갤러리 선택
              </span>
              <input
                ref={galleryRef}
                type="file"
                accept="image/*"
                onChange={handleFile}
                style={{ display: 'none' }}
              />
            </label>
          </div>
        </div>
      )}

      {/* 에러 */}
      {error && (
        <div
          style={{
            backgroundColor: colors.dangerLight,
            borderRadius: radius.md,
            padding: '10px 14px',
            marginBottom: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <p style={{ color: colors.danger, fontSize: font.size.sm, flex: 1 }}>
            {error}
          </p>
          <button
            onClick={() => setError('')}
            style={{ background: 'none', border: 'none', color: colors.danger, cursor: 'pointer', fontSize: 16 }}
          >
            ×
          </button>
        </div>
      )}

      {/* 분석 시작 버튼 */}
      <button
        onClick={handleSubmit}
        disabled={!file}
        style={{
          width: '100%',
          padding: '15px',
          backgroundColor: file ? colors.accent : colors.bgSecondary,
          color: file ? '#fff' : colors.text3,
          border: 'none',
          borderRadius: radius.xl,
          fontSize: font.size.md,
          fontWeight: font.weight.semibold,
          cursor: file ? 'pointer' : 'not-allowed',
          transition: 'all 0.2s',
          marginBottom: 12,
        }}
      >
        {file ? '분석 시작' : '사진을 먼저 선택해 주세요'}
      </button>

      {/* 기록 바로가기 */}
      <button
        onClick={() => navigate('/records')}
        style={{
          width: '100%',
          padding: '13px',
          backgroundColor: 'transparent',
          color: colors.text2,
          border: `1.5px solid ${colors.divider}`,
          borderRadius: radius.xl,
          fontSize: font.size.sm,
          fontWeight: font.weight.medium,
          cursor: 'pointer',
        }}
      >
        내 분석 기록 보기
      </button>

      {showGuide && <ImageGuide type={type} onClose={() => setShowGuide(false)} />}
    </div>
  )
}
