import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../api/client'
import { useToast } from '../context/ToastContext'
import { colors, font, radius, shadow } from '../theme'

function validate(email: string, password: string, isRegister: boolean, nickname: string): string | null {
  if (!email.trim()) return '이메일을 입력해 주세요.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return '올바른 이메일 형식이 아닙니다.'
  if (!password) return '비밀번호를 입력해 주세요.'
  if (password.length < 6) return '비밀번호는 6자 이상이어야 합니다.'
  if (isRegister && nickname.length > 20) return '닉네임은 20자 이하로 입력해 주세요.'
  return null
}

export default function Login() {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [nickname, setNickname] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { show } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const err = validate(email, password, isRegister, nickname)
    if (err) { show(err, 'error'); return }

    setLoading(true)
    try {
      const res = isRegister
        ? await register(email.trim(), password, nickname.trim() || undefined)
        : await login(email.trim(), password)
      localStorage.setItem('access_token', res.data.access_token)
      show(isRegister ? '회원가입이 완료됐습니다!' : '로그인됐습니다.', 'success')
      navigate('/', { replace: true })
    } catch (err: any) {
      show(err.message ?? '오류가 발생했습니다.', 'error')
    } finally {
      setLoading(false)
    }
  }

  const switchTab = (reg: boolean) => {
    setIsRegister(reg)
    setEmail('')
    setPassword('')
    setNickname('')
  }

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: '32px 24px',
        backgroundColor: colors.bg,
      }}
    >
      {/* 로고 */}
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div
          style={{
            width: 68,
            height: 68,
            borderRadius: 18,
            backgroundColor: colors.accent,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            fontSize: 30,
            boxShadow: '0 8px 24px rgba(0,113,227,0.3)',
          }}
        >
          🔬
        </div>
        <h1
          style={{
            fontSize: font.size.xl,
            fontWeight: font.weight.bold,
            color: colors.text1,
            letterSpacing: '-0.02em',
            marginBottom: 6,
          }}
        >
          피부 AI 분석
        </h1>
        <p style={{ fontSize: font.size.sm, color: colors.text2 }}>
          두피·안면피부를 AI로 간편하게 분석하세요
        </p>
      </div>

      {/* 카드 */}
      <div
        style={{
          backgroundColor: colors.card,
          borderRadius: radius.xl,
          padding: '28px 24px',
          boxShadow: shadow.card,
        }}
      >
        {/* 탭 */}
        <div
          style={{
            display: 'flex',
            backgroundColor: colors.bg,
            borderRadius: radius.lg,
            padding: 3,
            marginBottom: 24,
          }}
        >
          {(['로그인', '회원가입'] as const).map((label, i) => (
            <button
              key={label}
              onClick={() => switchTab(i === 1)}
              style={{
                flex: 1,
                padding: '8px 0',
                borderRadius: radius.md,
                border: 'none',
                fontSize: font.size.md,
                fontWeight: font.weight.semibold,
                cursor: 'pointer',
                transition: 'all 0.2s',
                backgroundColor: isRegister === (i === 1) ? colors.card : 'transparent',
                color: isRegister === (i === 1) ? colors.text1 : colors.text2,
                boxShadow: isRegister === (i === 1) ? shadow.card : 'none',
              }}
            >
              {label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <input
            type="email"
            placeholder="이메일"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            disabled={loading}
            style={inputStyle(loading)}
          />
          <input
            type="password"
            placeholder="비밀번호 (6자 이상)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={isRegister ? 'new-password' : 'current-password'}
            disabled={loading}
            style={inputStyle(loading)}
          />
          {isRegister && (
            <input
              placeholder="닉네임 (선택)"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              disabled={loading}
              style={inputStyle(loading)}
            />
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: 6,
              padding: '14px',
              backgroundColor: loading ? colors.text3 : colors.accent,
              color: '#fff',
              border: 'none',
              borderRadius: radius.lg,
              fontSize: font.size.md,
              fontWeight: font.weight.semibold,
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            {loading && (
              <div style={{
                width: 16, height: 16, borderRadius: '50%',
                border: '2px solid rgba(255,255,255,0.4)',
                borderTop: '2px solid #fff',
                animation: 'spin 0.8s linear infinite',
              }} />
            )}
            {loading ? '처리 중...' : isRegister ? '가입하기' : '로그인'}
          </button>
        </form>
      </div>

      <p style={{ textAlign: 'center', fontSize: font.size.xs, color: colors.text3, marginTop: 24, lineHeight: 1.5 }}>
        본 서비스는 AI 보조 도구이며 의학적 진단이 아닙니다.
      </p>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

const inputStyle = (disabled: boolean): React.CSSProperties => ({
  padding: '13px 16px',
  backgroundColor: colors.bg,
  border: 'none',
  borderRadius: radius.md,
  fontSize: font.size.md,
  color: colors.text1,
  outline: 'none',
  opacity: disabled ? 0.6 : 1,
})
