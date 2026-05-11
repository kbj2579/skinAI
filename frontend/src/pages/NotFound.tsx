import { useNavigate } from 'react-router-dom'
import { colors, font, radius } from '../theme'

export default function NotFound() {
  const navigate = useNavigate()
  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 24px',
        backgroundColor: colors.bg,
        textAlign: 'center',
        minHeight: 400,
      }}
    >
      <div
        style={{
          fontSize: 64,
          marginBottom: 8,
          lineHeight: 1,
        }}
      >
        🔍
      </div>
      <h1
        style={{
          fontSize: font.size.xxl,
          fontWeight: font.weight.bold,
          color: colors.text1,
          letterSpacing: '-0.02em',
          marginBottom: 8,
        }}
      >
        404
      </h1>
      <p style={{ fontSize: font.size.md, color: colors.text2, marginBottom: 28, lineHeight: 1.5 }}>
        페이지를 찾을 수 없습니다
      </p>
      <button
        onClick={() => navigate('/', { replace: true })}
        style={{
          padding: '14px 32px',
          backgroundColor: colors.accent,
          color: '#fff',
          border: 'none',
          borderRadius: radius.xl,
          fontSize: font.size.md,
          fontWeight: font.weight.semibold,
          cursor: 'pointer',
        }}
      >
        홈으로
      </button>
    </div>
  )
}
