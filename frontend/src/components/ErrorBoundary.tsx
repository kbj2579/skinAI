import { Component, ErrorInfo, ReactNode } from 'react'
import { colors, font, radius } from '../theme'

interface Props { children: ReactNode }
interface State { hasError: boolean; error?: Error }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error.message, info.componentStack)
  }

  render() {
    if (!this.state.hasError) return this.props.children

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
        }}
      >
        <div style={{ fontSize: 52, marginBottom: 16 }}>⚠️</div>
        <h2
          style={{
            fontSize: font.size.xl,
            fontWeight: font.weight.bold,
            color: colors.text1,
            marginBottom: 8,
            letterSpacing: '-0.02em',
          }}
        >
          문제가 발생했습니다
        </h2>
        <p style={{ fontSize: font.size.md, color: colors.text2, marginBottom: 28, lineHeight: 1.5 }}>
          일시적인 오류입니다.{'\n'}앱을 새로고침하면 해결됩니다.
        </p>
        <button
          onClick={() => window.location.reload()}
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
          새로고침
        </button>
      </div>
    )
  }
}
