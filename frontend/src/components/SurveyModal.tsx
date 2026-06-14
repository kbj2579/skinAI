import { useState, useEffect } from 'react'
import { colors, font, radius, shadow } from '../theme'
import { listCosmetics, listRecords } from '../api/client'

export interface CosmeticEntry {
  productName: string
  startDate: string
}

export interface SurveyData {
  bodyPart: string
  smoking: boolean | null
  drinking: boolean | null
  symptomDescription: string
  skinType: string
  cosmetics: CosmeticEntry[]
  linkedAnalysisId?: number
}

const BODY_PARTS = ['얼굴', '팔', '다리', '등', '가슴', '배']
const SKIN_TYPES = ['지성', '건성', '복합성', '민감성', '중성']
const RISK_LABELS: Record<string, string> = { normal: '정상', mild: '경미', suspicious: '주의', danger: '위험' }
const RISK_COLORS: Record<string, string> = { normal: '#4CAF50', mild: '#FF9800', suspicious: '#FF5722', danger: '#F44336' }

interface SavedCosmetic { id: number; product_name: string; start_date: string }
interface PrevLesionRecord { id: number; created_at: string; risk_level: string; body_part: string | null }

interface Props {
  analysisType?: 'skin' | 'lesion'
  onConfirm: (data: SurveyData) => void
  onClose: () => void
}

const today = new Date().toISOString().split('T')[0]

export default function SurveyModal({ analysisType = 'skin', onConfirm, onClose }: Props) {
  const isSkin = analysisType === 'skin'
  const isLesion = analysisType === 'lesion'

  // Step 1
  const [step, setStep] = useState<1 | 2>(1)
  const [bodyPart, setBodyPart] = useState('')
  const [smoking, setSmoking] = useState<boolean | null>(null)
  const [drinking, setDrinking] = useState<boolean | null>(null)
  const [symptomDescription, setSymptomDescription] = useState('')
  const [skinType, setSkinType] = useState('')
  const [cosmetics, setCosmetics] = useState<CosmeticEntry[]>([])
  const [newProduct, setNewProduct] = useState('')
  const [newStartDate, setNewStartDate] = useState(today)

  // Saved cosmetics quick-select (skin)
  const [savedCosmetics, setSavedCosmetics] = useState<SavedCosmetic[]>([])
  const [selectedSavedIds, setSelectedSavedIds] = useState<Set<number>>(new Set())

  // Step 2 (lesion)
  const [isLinkedLesion, setIsLinkedLesion] = useState<boolean | null>(null)
  const [prevRecords, setPrevRecords] = useState<PrevLesionRecord[]>([])
  const [linkedAnalysisId, setLinkedAnalysisId] = useState<number | undefined>()
  const [loadingPrev, setLoadingPrev] = useState(false)

  const step1Valid = bodyPart !== '' && smoking !== null && drinking !== null

  useEffect(() => {
    if (isSkin) {
      listCosmetics().then((res) => setSavedCosmetics(res.data)).catch(() => {})
    }
  }, [isSkin])

  const goToStep2 = () => {
    setStep(2)
    setLoadingPrev(true)
    listRecords('lesion', 8, 0)
      .then((res) => {
        const data = res.data
        setPrevRecords(Array.isArray(data) ? data : (data.items ?? []))
      })
      .catch(() => setPrevRecords([]))
      .finally(() => setLoadingPrev(false))
  }

  const toggleSavedCosmetic = (c: SavedCosmetic) => {
    const next = new Set(selectedSavedIds)
    if (next.has(c.id)) {
      next.delete(c.id)
    } else {
      next.add(c.id)
    }
    setSelectedSavedIds(next)
  }

  const handleAddCosmetic = () => {
    if (!newProduct.trim()) return
    setCosmetics((prev) => [...prev, { productName: newProduct.trim(), startDate: newStartDate }])
    setNewProduct('')
    setNewStartDate(today)
  }

  const handleRemoveCosmetic = (idx: number) => {
    setCosmetics((prev) => prev.filter((_, i) => i !== idx))
  }

  const handleConfirm = () => {
    onConfirm({
      bodyPart,
      smoking: smoking!,
      drinking: drinking!,
      symptomDescription: symptomDescription.trim(),
      skinType,
      cosmetics,
      linkedAnalysisId,
    })
  }

  const btnStyle = (active: boolean) => ({
    padding: '10px 6px',
    borderRadius: radius.md,
    border: `1.5px solid ${active ? colors.accent : colors.border}`,
    backgroundColor: active ? colors.accentLight : colors.bg,
    color: active ? colors.accent : colors.text2,
    fontSize: font.size.sm,
    fontWeight: active ? font.weight.semibold : font.weight.regular,
    cursor: 'pointer' as const,
    transition: 'all 0.15s',
  })

  return (
    <div
      style={{
        position: 'fixed', inset: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
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
          maxHeight: '90vh',
          overflowY: 'auto',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 핸들 */}
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 12, marginBottom: 20 }}>
          <div style={{ width: 36, height: 4, backgroundColor: colors.border, borderRadius: 2 }} />
        </div>

        {step === 1 ? (
          <>
            <h3 style={{ fontSize: font.size.lg, fontWeight: font.weight.bold, color: colors.text1, marginBottom: 4 }}>
              분석 전 설문
            </h3>
            <p style={{ fontSize: font.size.sm, color: colors.text2, marginBottom: 20 }}>
              정확한 분석을 위해 간단한 정보를 입력해 주세요
            </p>

            {/* 분석 부위 */}
            <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, marginBottom: 10 }}>
              분석 부위
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 20 }}>
              {BODY_PARTS.map((part) => (
                <button key={part} onClick={() => setBodyPart(part)} style={btnStyle(bodyPart === part)}>
                  {part}
                </button>
              ))}
            </div>

            {/* 피부 타입 (skin만) */}
            {isSkin && (
              <>
                <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 10 }}>
                  <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, margin: 0 }}>피부 타입</p>
                  <span style={{ fontSize: font.size.xs, color: colors.text3 }}>선택 입력</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 20 }}>
                  {SKIN_TYPES.map((t) => (
                    <button key={t} onClick={() => setSkinType(skinType === t ? '' : t)} style={btnStyle(skinType === t)}>
                      {t}
                    </button>
                  ))}
                </div>
              </>
            )}

            {/* 증상 설명 (skin만) */}
            {isSkin && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 10 }}>
                  <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, margin: 0 }}>증상 설명</p>
                  <span style={{ fontSize: font.size.xs, color: colors.text3 }}>선택 입력</span>
                </div>
                <textarea
                  value={symptomDescription}
                  onChange={(e) => setSymptomDescription(e.target.value.slice(0, 500))}
                  placeholder="예: 최근 볼 주변이 붉고 따가워요."
                  rows={3}
                  style={{
                    width: '100%', boxSizing: 'border-box', resize: 'none',
                    padding: '12px 14px', borderRadius: radius.md,
                    border: `1.5px solid ${symptomDescription.trim() ? colors.accent : colors.border}`,
                    backgroundColor: symptomDescription.trim() ? colors.accentLight : colors.bg,
                    color: colors.text1, fontSize: font.size.sm, lineHeight: 1.45, outline: 'none',
                  }}
                />
                <p style={{ marginTop: 6, marginBottom: 0, fontSize: font.size.xs, color: colors.text3, textAlign: 'right' }}>
                  {symptomDescription.length}/500
                </p>
              </div>
            )}

            {/* 화장품 (skin만) */}
            {isSkin && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 10 }}>
                  <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, margin: 0 }}>사용 중인 화장품</p>
                  <span style={{ fontSize: font.size.xs, color: colors.text3 }}>선택 입력</span>
                </div>

                {/* 이전에 등록한 화장품 빠른 선택 */}
                {savedCosmetics.length > 0 && (
                  <div style={{ marginBottom: 12 }}>
                    <p style={{ fontSize: font.size.xs, color: colors.text3, marginBottom: 8 }}>이전에 등록한 화장품</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {savedCosmetics.map((c) => {
                        const selected = selectedSavedIds.has(c.id)
                        return (
                          <button
                            key={c.id}
                            onClick={() => toggleSavedCosmetic(c)}
                            style={{
                              padding: '6px 12px', borderRadius: radius.pill,
                              border: `1.5px solid ${selected ? colors.accent : colors.border}`,
                              backgroundColor: selected ? colors.accentLight : colors.bg,
                              color: selected ? colors.accent : colors.text2,
                              fontSize: font.size.xs,
                              fontWeight: selected ? font.weight.semibold : font.weight.regular,
                              cursor: 'pointer',
                            }}
                          >
                            {selected ? '✓ ' : ''}{c.product_name}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* 새로 추가된 화장품 목록 */}
                {cosmetics.map((c, idx) => (
                  <div key={idx} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    backgroundColor: colors.accentLight, borderRadius: radius.md,
                    padding: '8px 12px', marginBottom: 6,
                  }}>
                    <div>
                      <span style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.accent }}>{c.productName}</span>
                      <span style={{ fontSize: font.size.xs, color: colors.text3, marginLeft: 8 }}>{c.startDate} 부터</span>
                    </div>
                    <button onClick={() => handleRemoveCosmetic(idx)} style={{ background: 'none', border: 'none', color: colors.text3, cursor: 'pointer', fontSize: 16 }}>×</button>
                  </div>
                ))}

                {/* 새 화장품 입력 */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                  <input
                    type="text"
                    placeholder="새 제품명"
                    value={newProduct}
                    onChange={(e) => setNewProduct(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleAddCosmetic() }}
                    style={{
                      flex: 1, padding: '10px 12px', borderRadius: radius.md,
                      border: `1.5px solid ${colors.border}`, backgroundColor: colors.bg,
                      fontSize: font.size.sm, color: colors.text1, outline: 'none',
                    }}
                  />
                  <input
                    type="date"
                    value={newStartDate}
                    onChange={(e) => setNewStartDate(e.target.value)}
                    style={{
                      width: 130, padding: '10px 8px', borderRadius: radius.md,
                      border: `1.5px solid ${colors.border}`, backgroundColor: colors.bg,
                      fontSize: font.size.sm, color: colors.text1, outline: 'none',
                    }}
                  />
                </div>
                <button
                  onClick={handleAddCosmetic}
                  disabled={!newProduct.trim()}
                  style={{
                    width: '100%', padding: '9px', borderRadius: radius.md,
                    border: `1.5px solid ${colors.accent}`,
                    backgroundColor: 'transparent', color: colors.accent,
                    fontSize: font.size.sm, fontWeight: font.weight.semibold,
                    cursor: newProduct.trim() ? 'pointer' : 'not-allowed',
                    opacity: newProduct.trim() ? 1 : 0.4,
                  }}
                >
                  + 화장품 추가
                </button>
              </div>
            )}

            {/* 흡연 여부 */}
            <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, marginBottom: 10 }}>흡연 여부</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 20 }}>
              {[{ label: '흡연', value: true }, { label: '비흡연', value: false }].map((opt) => (
                <button key={String(opt.value)} onClick={() => setSmoking(opt.value)} style={btnStyle(smoking === opt.value)}>
                  {opt.label}
                </button>
              ))}
            </div>

            {/* 음주 여부 */}
            <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, marginBottom: 10 }}>음주 여부</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 24 }}>
              {[{ label: '음주', value: true }, { label: '비음주', value: false }].map((opt) => (
                <button key={String(opt.value)} onClick={() => setDrinking(opt.value)} style={btnStyle(drinking === opt.value)}>
                  {opt.label}
                </button>
              ))}
            </div>

            {/* 확인 / 다음 */}
            <button
              onClick={isLesion ? goToStep2 : handleConfirm}
              disabled={!step1Valid}
              style={{
                width: '100%', padding: '15px', borderRadius: radius.xl, border: 'none',
                backgroundColor: step1Valid ? colors.accent : colors.bgSecondary,
                color: step1Valid ? '#fff' : colors.text3,
                fontSize: font.size.md, fontWeight: font.weight.semibold,
                cursor: step1Valid ? 'pointer' : 'not-allowed', transition: 'all 0.2s',
              }}
            >
              {!step1Valid ? '모든 항목을 선택해 주세요' : isLesion ? '다음' : '사진 선택하기'}
            </button>
          </>
        ) : (
          // Step 2: 이전 병변 연결
          <>
            <button
              onClick={() => setStep(1)}
              style={{ background: 'none', border: 'none', color: colors.accent, fontSize: 20, cursor: 'pointer', padding: 0, marginBottom: 16, lineHeight: 1 }}
            >
              ‹ 이전
            </button>
            <h3 style={{ fontSize: font.size.lg, fontWeight: font.weight.bold, color: colors.text1, marginBottom: 4 }}>
              이전에 기록한 병변인가요?
            </h3>
            <p style={{ fontSize: font.size.sm, color: colors.text2, marginBottom: 20 }}>
              같은 병변이라면 연결해서 변화를 추적할 수 있어요
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 20 }}>
              <button
                onClick={() => { setIsLinkedLesion(true); setLinkedAnalysisId(undefined) }}
                style={{
                  padding: '16px 8px', borderRadius: radius.lg, cursor: 'pointer',
                  border: `1.5px solid ${isLinkedLesion === true ? colors.accent : colors.border}`,
                  backgroundColor: isLinkedLesion === true ? colors.accentLight : colors.bg,
                  color: isLinkedLesion === true ? colors.accent : colors.text2,
                  fontSize: font.size.sm, fontWeight: font.weight.semibold,
                }}
              >
                예, 이전 기록이에요
              </button>
              <button
                onClick={() => { setIsLinkedLesion(false); setLinkedAnalysisId(undefined) }}
                style={{
                  padding: '16px 8px', borderRadius: radius.lg, cursor: 'pointer',
                  border: `1.5px solid ${isLinkedLesion === false ? colors.accent : colors.border}`,
                  backgroundColor: isLinkedLesion === false ? colors.accentLight : colors.bg,
                  color: isLinkedLesion === false ? colors.accent : colors.text2,
                  fontSize: font.size.sm, fontWeight: font.weight.semibold,
                }}
              >
                아니요, 새 병변이에요
              </button>
            </div>

            {/* 이전 기록 목록 */}
            {isLinkedLesion === true && (
              <div style={{ marginBottom: 20 }}>
                <p style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.text1, marginBottom: 10 }}>
                  이전 분석 기록을 선택해 주세요
                </p>
                {loadingPrev ? (
                  <p style={{ fontSize: font.size.sm, color: colors.text3, textAlign: 'center', padding: '20px 0' }}>불러오는 중...</p>
                ) : prevRecords.length === 0 ? (
                  <p style={{ fontSize: font.size.sm, color: colors.text3, textAlign: 'center', padding: '20px 0' }}>이전 병변 기록이 없어요</p>
                ) : (
                  prevRecords.map((r) => {
                    const selected = linkedAnalysisId === r.id
                    const riskColor = RISK_COLORS[r.risk_level] ?? colors.text2
                    const riskLabel = RISK_LABELS[r.risk_level] ?? r.risk_level
                    return (
                      <button
                        key={r.id}
                        onClick={() => setLinkedAnalysisId(selected ? undefined : r.id)}
                        style={{
                          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          padding: '12px 14px', borderRadius: radius.md, marginBottom: 8,
                          border: `1.5px solid ${selected ? colors.accent : colors.border}`,
                          backgroundColor: selected ? colors.accentLight : colors.bg,
                          cursor: 'pointer', textAlign: 'left',
                        }}
                      >
                        <div>
                          <p style={{ margin: 0, fontSize: font.size.sm, fontWeight: font.weight.semibold, color: selected ? colors.accent : colors.text1 }}>
                            {new Date(r.created_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' })}
                          </p>
                          <p style={{ margin: '2px 0 0', fontSize: font.size.xs, color: colors.text3 }}>
                            {r.body_part ?? '부위 미기록'}
                          </p>
                        </div>
                        <span style={{
                          fontSize: font.size.xs, fontWeight: font.weight.semibold,
                          color: riskColor, padding: '3px 10px', borderRadius: radius.pill,
                          backgroundColor: riskColor + '20',
                        }}>
                          {riskLabel}
                        </span>
                      </button>
                    )
                  })
                )}
              </div>
            )}

            <button
              onClick={handleConfirm}
              disabled={isLinkedLesion === null}
              style={{
                width: '100%', padding: '15px', borderRadius: radius.xl, border: 'none',
                backgroundColor: isLinkedLesion !== null ? colors.accent : colors.bgSecondary,
                color: isLinkedLesion !== null ? '#fff' : colors.text3,
                fontSize: font.size.md, fontWeight: font.weight.semibold,
                cursor: isLinkedLesion !== null ? 'pointer' : 'not-allowed', transition: 'all 0.2s',
              }}
            >
              {isLinkedLesion === null ? '선택해 주세요' : '사진 선택하기'}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
