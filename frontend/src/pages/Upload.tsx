import { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { analyze, AnalysisType, listLesionTracks, createLesionTrack } from '../api/client'
import ImageGuide from '../components/ImageGuide'
import SurveyModal, { SurveyData } from '../components/SurveyModal'
import { useToast } from '../context/ToastContext'
import { colors, font, radius, shadow } from '../theme'
import { TYPE_LABELS } from '../utils/skinHelpers'

const MAX_FILE_SIZE = 20 * 1024 * 1024
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif']

// 로딩 단계
const LOADING_STEPS = [
  { icon: '🗜️', label: '이미지 전처리 중...' },
  { icon: '📡', label: '서버 전송 중...' },
  { icon: '🤖', label: 'AI 분석 중...' },
]

const TARGET_SIZE = 512

// ── 밝기 자동 보정 ────────────────────────────────────────────────
// 평균 휘도를 계산해 너무 어둡거나 밝으면 보정 계수를 적용합니다.
function adjustBrightness(ctx: CanvasRenderingContext2D, w: number, h: number) {
  const imageData = ctx.getImageData(0, 0, w, h)
  const data = imageData.data
  const pixelCount = data.length / 4

  let total = 0
  for (let i = 0; i < data.length; i += 4) {
    // 인간 시각 가중치 (ITU-R BT.601)
    total += 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]
  }
  const avg = total / pixelCount   // 0~255

  // 보정 계수: 목표 휘도 110 기준
  let factor = 1
  if      (avg < 50)  factor = 1.50   // 매우 어두움
  else if (avg < 80)  factor = 1.25   // 어두움
  else if (avg < 100) factor = 1.10   // 약간 어두움
  else if (avg > 210) factor = 0.75   // 매우 밝음
  else if (avg > 180) factor = 0.88   // 밝음
  else if (avg > 155) factor = 0.95   // 약간 밝음

  if (factor !== 1) {
    for (let i = 0; i < data.length; i += 4) {
      data[i]     = Math.min(255, data[i]     * factor)
      data[i + 1] = Math.min(255, data[i + 1] * factor)
      data[i + 2] = Math.min(255, data[i + 2] * factor)
    }
    ctx.putImageData(imageData, 0, 0)
  }
}

// ── 이미지 전처리 ─────────────────────────────────────────────────
// 1) EXIF 방향 자동 보정 (createImageBitmap이 처리)
// 2) 센터 크롭 → 정사각형 (비율 유지)
// 3) 1024×1024 리사이즈
// 4) 밝기 자동 보정
async function preprocessImage(file: File): Promise<Blob> {
  // createImageBitmap: 브라우저가 EXIF orientation을 자동 적용
  const bitmap = await createImageBitmap(file)

  const sw = bitmap.width
  const sh = bitmap.height
  const cropSize = Math.min(sw, sh)           // 짧은 변 기준 정사각형
  const sx = Math.floor((sw - cropSize) / 2)  // 가로 중앙
  const sy = Math.floor((sh - cropSize) / 2)  // 세로 중앙

  const canvas = document.createElement('canvas')
  canvas.width  = TARGET_SIZE
  canvas.height = TARGET_SIZE
  const ctx = canvas.getContext('2d')!

  // 센터 크롭 + 리사이즈 (한 번에)
  ctx.drawImage(bitmap, sx, sy, cropSize, cropSize, 0, 0, TARGET_SIZE, TARGET_SIZE)
  bitmap.close()

  // 밝기 자동 보정
  adjustBrightness(ctx, TARGET_SIZE, TARGET_SIZE)

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => { if (blob) resolve(blob); else reject(new Error('이미지 변환 실패')) },
      'image/jpeg',
      0.88,
    )
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

  // 설문 모달
  const [showSurvey, setShowSurvey] = useState(false)
  const [pendingCapture, setPendingCapture] = useState<'camera' | 'gallery' | null>(null)
  const [survey, setSurvey] = useState<SurveyData | null>(null)

  const cameraRef = useRef<HTMLInputElement>(null)
  const galleryRef = useRef<HTMLInputElement>(null)

  // 카메라 자동 촬영
  const [showFaceCamera, setShowFaceCamera] = useState(false)
  const [qualBright, setQualBright] = useState(false)
  const [qualSharp, setQualSharp] = useState(false)
  const [qualStable, setQualStable] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const rafRef = useRef<number>(0)
  const stableRef = useRef(0)
  const capturedRef = useRef(false)
  const prevPixelsRef = useRef<Uint8ClampedArray | null>(null)

  const [tracks, setTracks] = useState<LesionTrack[]>([])
  const [selectedTrackId, setSelectedTrackId] = useState<number | undefined>()
  const [newTrackName, setNewTrackName] = useState('')
  const [creatingTrack, setCreatingTrack] = useState(false)
  const { show } = useToast()

  // 페이지 진입 시 상태 초기화
  useEffect(() => {
    setPreview(null)
    setFile(null)
    setError('')
    setLoadingStep(0)
    setSurvey(null)
  }, [location.key])

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    cancelAnimationFrame(rafRef.current)
    setShowFaceCamera(false)
    setQualBright(false)
    setQualSharp(false)
    setQualStable(false)
    stableRef.current = 0
    capturedRef.current = false
    prevPixelsRef.current = null
  }, [])

  useEffect(() => () => stopCamera(), [stopCamera])

  const captureFrame = useCallback(() => {
    const video = videoRef.current
    if (!video) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d')!.drawImage(video, 0, 0)
    canvas.toBlob((blob) => {
      if (!blob) return
      stopCamera()
      const f = new File([blob], 'face_capture.jpg', { type: 'image/jpeg' })
      setFile(f)
      setPreview(URL.createObjectURL(f))
      show('얼굴이 촬영됐습니다.', 'success')
    }, 'image/jpeg', 0.95)
  }, [stopCamera, show])

  const startFaceCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
      })
      streamRef.current = stream
      setShowFaceCamera(true)

      const W = 160, H = 120
      const offscreen = document.createElement('canvas')
      offscreen.width = W
      offscreen.height = H
      const offCtx = offscreen.getContext('2d')!

      const loop = () => {
        if (capturedRef.current) return
        const video = videoRef.current
        if (!video || video.readyState < 2) {
          rafRef.current = requestAnimationFrame(loop)
          return
        }

        offCtx.drawImage(video, 0, 0, W, H)
        const { data } = offCtx.getImageData(0, 0, W, H)
        const N = W * H

        // 밝기
        let lumaSum = 0
        for (let i = 0; i < data.length; i += 4) {
          lumaSum += 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]
        }
        const avgLuma = lumaSum / N
        const bright = avgLuma >= 50 && avgLuma <= 210

        // 선명도 (분산)
        let varSum = 0
        for (let i = 0; i < data.length; i += 4) {
          const l = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]
          varSum += (l - avgLuma) ** 2
        }
        const sharp = varSum / N > 180

        // 안정성 (프레임 간 차이)
        const prev = prevPixelsRef.current
        let diffSum = 0
        if (prev) {
          for (let i = 0; i < data.length; i += 4) {
            diffSum += Math.abs(data[i] - prev[i])
              + Math.abs(data[i + 1] - prev[i + 1])
              + Math.abs(data[i + 2] - prev[i + 2])
          }
          diffSum /= N * 3
        }
        const stable = !prev || diffSum < 12
        prevPixelsRef.current = new Uint8ClampedArray(data)

        setQualBright(bright)
        setQualSharp(sharp)
        setQualStable(stable)

        if (bright && sharp && stable) {
          stableRef.current += 1
          if (stableRef.current >= 20) {
            capturedRef.current = true
            captureFrame()
            return
          }
        } else {
          stableRef.current = 0
        }

        rafRef.current = requestAnimationFrame(loop)
      }

      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.play().then(() => {
            rafRef.current = requestAnimationFrame(loop)
          })
        }
      }, 50)
    } catch {
      show('카메라에 접근할 수 없습니다. 기본 카메라를 사용합니다.', 'error')
      cameraRef.current?.click()
    }
  }, [captureFrame, show])

  // 분석 유형 변경 시 저장 + 병변 트랙 로드
  useEffect(() => {
    localStorage.setItem('last_analysis_type', type)
    if (type === 'lesion') {
      listLesionTracks().then((res) => setTracks(res.data)).catch(() => setTracks([]))
    }
  }, [type])

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
    setSurvey(null)
  }

  // 카메라/갤러리 버튼 클릭 → 설문 먼저
  const handleCaptureClick = (mode: 'camera' | 'gallery') => {
    setPendingCapture(mode)
    setShowSurvey(true)
  }

  // 설문 완료 → 실제 파일 선택 열기
  const handleSurveyConfirm = (data: SurveyData) => {
    setSurvey(data)
    setShowSurvey(false)
    setTimeout(() => {
      if (pendingCapture === 'camera' && type === 'skin') {
        startFaceCamera()
      } else if (pendingCapture === 'camera') {
        cameraRef.current?.click()
      } else {
        galleryRef.current?.click()
      }
      setPendingCapture(null)
    }, 100)
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
      resized = await preprocessImage(file)
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
      const res = await analyze(type, resized, {
        trackId: type === 'lesion' ? selectedTrackId : undefined,
        bodyPart: survey?.bodyPart,
        smoking: survey?.smoking ?? undefined,
        drinking: survey?.drinking ?? undefined,
        symptomDescription: survey?.symptomDescription,
      })
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

      {/* 헤더 */}
      <div style={{ marginBottom: 20 }}>
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
            <button
              onClick={() => handleCaptureClick('camera')}
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
                border: 'none',
              }}
            >
              <span style={{ fontSize: 32 }}>📷</span>
              <span style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: '#fff' }}>
                카메라 촬영
              </span>
            </button>
            {/* 숨김 input — 설문 완료 후 programmatically 열림 */}
            <input ref={cameraRef} type="file" accept="image/*" capture="environment" onChange={handleFile} style={{ display: 'none' }} />

            {/* 갤러리 선택 */}
            <button
              onClick={() => handleCaptureClick('gallery')}
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
            </button>
            {/* 숨김 input — 설문 완료 후 programmatically 열림 */}
            <input ref={galleryRef} type="file" accept="image/*" onChange={handleFile} style={{ display: 'none' }} />
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

      {/* 선택된 설문 요약 */}
      {survey && (
        <div style={{
          display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12,
        }}>
          {[
            survey.bodyPart,
            survey.smoking ? '흡연' : '비흡연',
            survey.drinking ? '음주' : '비음주',
            survey.symptomDescription ? `증상: ${survey.symptomDescription.slice(0, 18)}${survey.symptomDescription.length > 18 ? '...' : ''}` : null,
          ].filter((tag): tag is string => Boolean(tag)).map((tag) => (
            <span key={tag} style={{
              fontSize: font.size.xs,
              color: colors.accent,
              backgroundColor: colors.accentLight,
              borderRadius: radius.pill,
              padding: '3px 10px',
              fontWeight: font.weight.semibold,
            }}>
              {tag}
            </span>
          ))}
          <button
            onClick={() => setSurvey(null)}
            style={{ background: 'none', border: 'none', fontSize: font.size.xs, color: colors.text3, cursor: 'pointer' }}
          >
            수정
          </button>
        </div>
      )}

      {showGuide && <ImageGuide type={type} onClose={() => setShowGuide(false)} />}
      {showSurvey && (
        <SurveyModal
          analysisType={type}
          onConfirm={handleSurveyConfirm}
          onClose={() => { setShowSurvey(false); setPendingCapture(null) }}
        />
      )}

      {/* 카메라 오버레이 */}
      {showFaceCamera && (() => {
        const allGood = qualBright && qualSharp && qualStable
        return (
          <div style={{ position: 'fixed', inset: 0, backgroundColor: '#000', zIndex: 3000 }}>
            <video ref={videoRef} playsInline muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />

            {/* 타원 가이드 */}
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
              <div style={{
                width: 220, height: 280,
                border: `3px solid ${allGood ? '#4CAF50' : 'rgba(255,255,255,0.65)'}`,
                borderRadius: '50%',
                boxShadow: allGood ? '0 0 28px rgba(76,175,80,0.7)' : 'none',
                transition: 'border-color 0.2s, box-shadow 0.2s',
              }} />
            </div>

            {/* 품질 지표 */}
            <div style={{ position: 'absolute', bottom: 130, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 10 }}>
              {([
                { ok: qualBright, label: '밝기', icon: '☀️' },
                { ok: qualSharp,  label: '선명도', icon: '🔍' },
                { ok: qualStable, label: '안정',  icon: '✋' },
              ] as const).map(({ ok, label, icon }) => (
                <div key={label} style={{
                  display: 'flex', alignItems: 'center', gap: 4,
                  padding: '5px 12px', borderRadius: 20,
                  backgroundColor: ok ? 'rgba(76,175,80,0.85)' : 'rgba(0,0,0,0.55)',
                  backdropFilter: 'blur(4px)',
                  transition: 'background-color 0.2s',
                }}>
                  <span style={{ fontSize: 13 }}>{icon}</span>
                  <span style={{ color: '#fff', fontSize: 12, fontWeight: 600 }}>{label}</span>
                </div>
              ))}
            </div>

            {/* 수동 촬영 버튼 */}
            <button
              onClick={() => { if (!capturedRef.current) { capturedRef.current = true; captureFrame() } }}
              style={{
                position: 'absolute', bottom: 48,
                left: '50%', transform: 'translateX(-50%)',
                width: 72, height: 72, borderRadius: '50%',
                backgroundColor: '#fff', border: '4px solid rgba(255,255,255,0.4)',
                cursor: 'pointer', boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
              }}
            />

            {/* 닫기 버튼 */}
            <button onClick={stopCamera} style={{ position: 'absolute', top: 20, right: 20, backgroundColor: 'rgba(0,0,0,0.5)', color: '#fff', border: 'none', borderRadius: '50%', width: 44, height: 44, fontSize: 22, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              ×
            </button>
          </div>
        )
      })()}
    </div>
  )
}
