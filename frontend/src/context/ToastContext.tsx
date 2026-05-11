import { createContext, useCallback, useContext, useState, ReactNode } from 'react'
import { colors, font, radius, shadow } from '../theme'

type ToastType = 'success' | 'error' | 'info' | 'warning'
interface ToastItem { id: string; message: string; type: ToastType }
interface ToastCtx { show: (message: string, type?: ToastType) => void }

const ToastContext = createContext<ToastCtx>({ show: () => {} })
export const useToast = () => useContext(ToastContext)

const STYLES: Record<ToastType, { bg: string; icon: string }> = {
  success: { bg: colors.success, icon: '✓' },
  error:   { bg: colors.danger,  icon: '✕' },
  warning: { bg: colors.warning, icon: '!' },
  info:    { bg: colors.accent,  icon: 'ℹ' },
}

function ToastItem({ item }: { item: ToastItem }) {
  const s = STYLES[item.type]
  return (
    <div
      style={{
        backgroundColor: s.bg,
        color: '#fff',
        borderRadius: radius.lg,
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        boxShadow: shadow.strong,
        fontSize: font.size.sm,
        fontWeight: font.weight.medium,
        animation: 'toast-slide-up 0.28s cubic-bezier(.22,.68,0,1.2) forwards',
        maxWidth: 340,
        wordBreak: 'keep-all',
      }}
    >
      <span
        style={{
          width: 22,
          height: 22,
          borderRadius: '50%',
          backgroundColor: 'rgba(255,255,255,0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 12,
          fontWeight: font.weight.bold,
          flexShrink: 0,
        }}
      >
        {s.icon}
      </span>
      <span style={{ flex: 1, lineHeight: 1.4 }}>{item.message}</span>
    </div>
  )
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const show = useCallback((message: string, type: ToastType = 'info') => {
    const id = `${Date.now()}-${Math.random()}`
    setToasts((prev) => [...prev.slice(-2), { id, message, type }])
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3200)
  }, [])

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <div
        style={{
          position: 'fixed',
          bottom: 88,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          zIndex: 9999,
          pointerEvents: 'none',
          alignItems: 'center',
        }}
      >
        {toasts.map((t) => <ToastItem key={t.id} item={t} />)}
      </div>
      <style>{`
        @keyframes toast-slide-up {
          from { opacity: 0; transform: translateY(16px) scale(0.95); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes shimmer {
          0%   { background-position: -200% 0; }
          100% { background-position:  200% 0; }
        }
        * { -webkit-tap-highlight-color: transparent; }
        ::-webkit-scrollbar { display: none; }
      `}</style>
    </ToastContext.Provider>
  )
}
