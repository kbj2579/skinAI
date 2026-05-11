import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMe, listRecords } from '../api/client'
import { useToast } from '../context/ToastContext'
import { colors, font, radius, shadow } from '../theme'

interface UserInfo { id: number; email: string; nickname: string | null }

export default function Profile() {
  const navigate = useNavigate()
  const { show } = useToast()
  const [user, setUser] = useState<UserInfo | null>(null)
  const [stats, setStats] = useState({ total: 0, skin: 0, scalp: 0, lesion: 0 })

  useEffect(() => {
    getMe().then((res) => setUser(res.data)).catch(() => {})

    // 분석 통계
    Promise.all([
      listRecords(undefined, 1, 0),
      listRecords('skin', 1, 0),
      listRecords('scalp', 1, 0),
      listRecords('lesion', 1, 0),
    ]).then(([all, skin, scalp, lesion]) => {
      const get = (r: any) => typeof r.data?.total === 'number' ? r.data.total : 0
      setStats({ total: get(all), skin: get(skin), scalp: get(scalp), lesion: get(lesion) })
    }).catch(() => {})
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('last_analysis_type')
    show('로그아웃됐습니다.', 'info')
    setTimeout(() => navigate('/login', { replace: true }), 500)
  }

  return (
    <div style={{ padding: '24px 16px 100px', backgroundColor: colors.bg, minHeight: '100%' }}>
      {/* 헤더 */}
      <h1
        style={{
          fontSize: font.size.xxl,
          fontWeight: font.weight.bold,
          color: colors.text1,
          letterSpacing: '-0.02em',
          marginBottom: 24,
        }}
      >
        프로필
      </h1>

      {/* 사용자 카드 */}
      <div
        style={{
          backgroundColor: colors.card,
          borderRadius: radius.xl,
          padding: '20px',
          marginBottom: 16,
          boxShadow: shadow.card,
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: radius.pill,
            backgroundColor: colors.accentLight,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 24,
            flexShrink: 0,
          }}
        >
          👤
        </div>
        <div>
          <p
            style={{
              fontSize: font.size.lg,
              fontWeight: font.weight.bold,
              color: colors.text1,
              marginBottom: 3,
            }}
          >
            {user?.nickname ?? '사용자'}
          </p>
          <p style={{ fontSize: font.size.sm, color: colors.text2 }}>
            {user?.email ?? '–'}
          </p>
        </div>
      </div>

      {/* 분석 통계 */}
      <div
        style={{
          backgroundColor: colors.card,
          borderRadius: radius.xl,
          padding: '16px 20px',
          marginBottom: 16,
          boxShadow: shadow.card,
        }}
      >
        <p
          style={{
            fontSize: font.size.xs,
            fontWeight: font.weight.semibold,
            color: colors.text2,
            marginBottom: 14,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          분석 통계
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {[
            { label: '전체', value: stats.total, color: colors.accent },
            { label: '안면피부', value: stats.skin, color: '#FF9500' },
            { label: '두피', value: stats.scalp, color: '#34C759' },
            { label: '병변', value: stats.lesion, color: '#FF3B30' },
          ].map((s) => (
            <div
              key={s.label}
              style={{
                backgroundColor: colors.bg,
                borderRadius: radius.lg,
                padding: '12px 14px',
                textAlign: 'center',
              }}
            >
              <p
                style={{
                  fontSize: font.size.xxl,
                  fontWeight: font.weight.bold,
                  color: s.color,
                  marginBottom: 2,
                }}
              >
                {s.value}
              </p>
              <p style={{ fontSize: font.size.xs, color: colors.text2 }}>{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 앱 정보 */}
      <div
        style={{
          backgroundColor: colors.card,
          borderRadius: radius.xl,
          overflow: 'hidden',
          marginBottom: 20,
          boxShadow: shadow.card,
        }}
      >
        {[
          { label: '서비스 버전', value: 'v1.0.0' },
          { label: '분석 엔진', value: 'Gemini 1.5 Flash' },
          { label: '데이터베이스', value: 'Supabase PostgreSQL' },
          { label: '이미지 저장소', value: 'Cloudflare R2' },
        ].map((item, i, arr) => (
          <div
            key={item.label}
            style={{
              padding: '13px 16px',
              borderBottom: i < arr.length - 1 ? `1px solid ${colors.divider}` : 'none',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: font.size.md, color: colors.text1 }}>{item.label}</span>
            <span style={{ fontSize: font.size.sm, color: colors.text2 }}>{item.value}</span>
          </div>
        ))}
      </div>

      {/* 면책 */}
      <p
        style={{
          fontSize: font.size.xs,
          color: colors.text3,
          lineHeight: 1.5,
          textAlign: 'center',
          marginBottom: 20,
          padding: '0 8px',
        }}
      >
        본 서비스는 AI 보조 분석 도구이며 의학적 진단을 대체하지 않습니다.
      </p>

      {/* 로그아웃 */}
      <button
        onClick={handleLogout}
        style={{
          width: '100%',
          padding: '14px',
          backgroundColor: colors.dangerLight,
          color: colors.danger,
          border: 'none',
          borderRadius: radius.xl,
          fontSize: font.size.md,
          fontWeight: font.weight.semibold,
          cursor: 'pointer',
        }}
      >
        로그아웃
      </button>
    </div>
  )
}
