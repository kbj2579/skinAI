import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ToastProvider } from './context/ToastContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import { NetworkBanner } from './components/NetworkBanner'
import Login from './pages/Login'
import Upload from './pages/Upload'
import Result from './pages/Result'
import Records from './pages/Records'
import RecordDetail from './pages/RecordDetail'
import Compare from './pages/Compare'
import Profile from './pages/Profile'
import NotFound from './pages/NotFound'
import { colors, font } from './theme'

function PrivateRoute({ children }: { children: JSX.Element }) {
  const token = localStorage.getItem('access_token')
  return token ? children : <Navigate to="/login" replace />
}

// ── 하단 탭 바 ─────────────────────────────────────────────────
const TABS = [
  { path: '/',        icon: '🔬', label: '분석'   },
  { path: '/records', icon: '📋', label: '기록'   },
  { path: '/profile', icon: '👤', label: '프로필' },
]

function BottomTabBar() {
  const location = useLocation()
  const navigate = useNavigate()
  const token = localStorage.getItem('access_token')
  if (!token) return null

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/' || location.pathname === '/result'
    return location.pathname.startsWith(path)
  }

  return (
    <div
      style={{
        height: 60,
        backgroundColor: colors.navBg,
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderTop: `1px solid ${colors.divider}`,
        display: 'flex',
        alignItems: 'center',
        flexShrink: 0,
        position: 'relative',
      }}
    >
      {TABS.map((tab) => {
        const active = isActive(tab.path)
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            aria-label={tab.label}
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 3,
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '6px 0 8px',
              color: active ? colors.accent : colors.text3,
              transition: 'color 0.15s',
              position: 'relative',
            }}
          >
            {active && (
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: 24,
                  height: 2.5,
                  backgroundColor: colors.accent,
                  borderRadius: '0 0 2px 2px',
                }}
              />
            )}
            <span style={{ fontSize: 22, lineHeight: 1 }}>{tab.icon}</span>
            <span
              style={{
                fontSize: font.size.xs,
                fontWeight: active ? font.weight.semibold : font.weight.regular,
                letterSpacing: '0.01em',
              }}
            >
              {tab.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}

// ── 라우트 ────────────────────────────────────────────────────
function AppRoutes() {
  const location = useLocation()
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<PrivateRoute><Upload key={location.key} /></PrivateRoute>} />
      <Route path="/result" element={<PrivateRoute><Result /></PrivateRoute>} />
      <Route path="/records" element={<PrivateRoute><Records /></PrivateRoute>} />
      <Route path="/records/:id" element={<PrivateRoute><RecordDetail /></PrivateRoute>} />
      <Route path="/compare/:trackId" element={<PrivateRoute><Compare /></PrivateRoute>} />
      <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

// ── 앱 루트 ───────────────────────────────────────────────────
export default function App() {
  return (
    <ToastProvider>
      <div
        style={{
          minHeight: '100vh',
          backgroundColor: '#E8E8ED',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start',
          padding: '28px 0',
        }}
      >
        <div
          style={{
            width: 390,
            minHeight: 844,
            backgroundColor: colors.bg,
            borderRadius: 44,
            boxShadow: '0 24px 80px rgba(0,0,0,0.28), 0 0 0 1px rgba(0,0,0,0.06)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Dynamic Island */}
          <div style={{ height: 36, backgroundColor: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <div style={{ width: 126, height: 22, backgroundColor: '#000', borderRadius: 20, border: '2px solid #1a1a1a' }} />
          </div>

          {/* 콘텐츠 */}
          <ErrorBoundary>
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', backgroundColor: colors.bg }}>
              <BrowserRouter>
                <NetworkBanner />
                <AppRoutes />
                <BottomTabBar />
              </BrowserRouter>
            </div>
          </ErrorBoundary>

          {/* 홈 인디케이터 */}
          <div style={{ height: 34, backgroundColor: colors.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <div style={{ width: 134, height: 5, backgroundColor: colors.text1, borderRadius: 3, opacity: 0.2 }} />
          </div>
        </div>
      </div>
    </ToastProvider>
  )
}
