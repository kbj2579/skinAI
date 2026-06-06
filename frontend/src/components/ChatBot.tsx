import { useState, useRef, useEffect, useCallback } from 'react'
import { useChatContext } from '../contexts/ChatContext'
import { sendChatMessage } from '../api/client'
import { colors, font, shadow } from '../theme'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatBot() {
  const { analysisId } = useChatContext()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, open])

  // 분석 결과가 바뀌면 대화 초기화
  useEffect(() => {
    setMessages([])
  }, [analysisId])

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    const newMessages: Message[] = [...messages, { role: 'user', content: text }]
    setInput('')
    setMessages(newMessages)
    setLoading(true)

    try {
      const res = await sendChatMessage(text, messages, analysisId ?? undefined)
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.reply }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '오류가 발생했습니다. 다시 시도해 주세요.' }])
    } finally {
      setLoading(false)
    }
  }, [input, loading, analysisId, messages])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <>
      {/* 플로팅 버튼 */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          style={{
            position: 'absolute',
            bottom: 76,
            right: 16,
            width: 52,
            height: 52,
            borderRadius: '50%',
            backgroundColor: colors.accent,
            color: '#fff',
            border: 'none',
            cursor: 'pointer',
            fontSize: 22,
            boxShadow: '0 4px 16px rgba(0,122,255,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          aria-label="AI 피부 상담"
        >
          💬
        </button>
      )}

      {/* 채팅 패널 */}
      {open && (
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: '72%',
            backgroundColor: colors.bg,
            borderRadius: '24px 24px 0 0',
            boxShadow: '0 -4px 24px rgba(0,0,0,0.15)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 200,
          }}
        >
          {/* 헤더 */}
          <div
            style={{
              padding: '16px 20px',
              borderBottom: `1px solid ${colors.divider}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexShrink: 0,
            }}
          >
            <div>
              <p style={{ fontSize: font.size.md, fontWeight: font.weight.semibold, color: colors.text1, margin: 0 }}>
                AI 피부 상담
              </p>
              {analysisId && (
                <p style={{ fontSize: font.size.xs, color: colors.accent, marginTop: 2, marginBottom: 0 }}>
                  분석 결과 기반 상담 중
                </p>
              )}
            </div>
            <button
              onClick={() => setOpen(false)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: 20,
                color: colors.text3,
                padding: '4px 8px',
              }}
            >
              ✕
            </button>
          </div>

          {/* 메시지 영역 */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', marginTop: 40, padding: '0 16px' }}>
                <p style={{ fontSize: 36, marginBottom: 12 }}>💬</p>
                <p style={{ fontSize: font.size.sm, color: colors.text2, lineHeight: 1.7, margin: 0 }}>
                  {analysisId
                    ? '분석 결과를 바탕으로\n병원 방문 여부, 관리법 등을\n자유롭게 물어보세요'
                    : '피부 건강에 대해\n무엇이든 물어보세요'}
                </p>
                <div
                  style={{
                    marginTop: 20,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 8,
                    alignItems: 'flex-start',
                  }}
                >
                  {(analysisId
                    ? ['병원에 꼭 가야 하나요?', '지금 당장 할 수 있는 관리법이 뭐예요?', '이 위험도는 심각한 건가요?']
                    : ['여드름에 좋은 음식이 뭐예요?', '자외선 차단제 언제 발라야 하나요?', '건성 피부 관리법 알려주세요']
                  ).map(q => (
                    <button
                      key={q}
                      onClick={() => { setInput(q); }}
                      style={{
                        padding: '8px 14px',
                        borderRadius: 20,
                        border: `1.5px solid ${colors.divider}`,
                        backgroundColor: colors.card,
                        color: colors.text2,
                        fontSize: font.size.xs,
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div
                  style={{
                    maxWidth: '82%',
                    padding: '10px 14px',
                    borderRadius: msg.role === 'user'
                      ? '18px 18px 4px 18px'
                      : '18px 18px 18px 4px',
                    backgroundColor: msg.role === 'user' ? colors.accent : colors.card,
                    color: msg.role === 'user' ? '#fff' : colors.text1,
                    fontSize: font.size.sm,
                    lineHeight: 1.65,
                    whiteSpace: 'pre-wrap',
                    boxShadow: shadow.card,
                  }}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div
                  style={{
                    padding: '10px 18px',
                    borderRadius: '18px 18px 18px 4px',
                    backgroundColor: colors.card,
                    fontSize: font.size.md,
                    color: colors.text3,
                    boxShadow: shadow.card,
                    letterSpacing: 4,
                  }}
                >
                  ···
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* 입력 영역 */}
          <div
            style={{
              padding: '12px 16px',
              borderTop: `1px solid ${colors.divider}`,
              display: 'flex',
              gap: 8,
              flexShrink: 0,
              backgroundColor: colors.bg,
            }}
          >
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="메시지를 입력하세요..."
              style={{
                flex: 1,
                padding: '10px 14px',
                borderRadius: 20,
                border: `1.5px solid ${colors.divider}`,
                backgroundColor: colors.bgSecondary,
                fontSize: font.size.sm,
                color: colors.text1,
                outline: 'none',
              }}
            />
            <button
              onClick={send}
              disabled={!input.trim() || loading}
              style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                backgroundColor: input.trim() && !loading ? colors.accent : colors.bgSecondary,
                color: input.trim() && !loading ? '#fff' : colors.text3,
                border: 'none',
                cursor: input.trim() && !loading ? 'pointer' : 'default',
                fontSize: 18,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'background-color 0.15s',
              }}
            >
              ↑
            </button>
          </div>
        </div>
      )}
    </>
  )
}
