import { useEffect, useState } from 'react'
import { colors, font } from '../theme'

export function NetworkBanner() {
  const [online, setOnline] = useState(navigator.onLine)
  const [wasOffline, setWasOffline] = useState(false)
  const [showRestored, setShowRestored] = useState(false)

  useEffect(() => {
    const handleOnline = () => {
      setOnline(true)
      if (wasOffline) {
        setShowRestored(true)
        setTimeout(() => setShowRestored(false), 2500)
      }
    }
    const handleOffline = () => {
      setOnline(false)
      setWasOffline(true)
    }
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [wasOffline])

  if (online && !showRestored) return null

  return (
    <div
      style={{
        backgroundColor: online ? colors.success : colors.danger,
        color: '#fff',
        padding: '8px 16px',
        textAlign: 'center',
        fontSize: font.size.sm,
        fontWeight: font.weight.semibold,
        letterSpacing: '0.01em',
        transition: 'background-color 0.3s',
        flexShrink: 0,
      }}
    >
      {online ? '✓  인터넷 연결이 복원됐습니다' : '📵  인터넷 연결이 없습니다'}
    </div>
  )
}
