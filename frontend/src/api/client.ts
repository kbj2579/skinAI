import axios, { AxiosError } from 'axios'

// ── JWT 만료 확인 ─────────────────────────────────────────────
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    // 10초 여유를 두고 만료 체크
    return typeof payload.exp === 'number' && payload.exp * 1000 < Date.now() + 10_000
  } catch {
    return true
  }
}

// ── Axios 인스턴스 ─────────────────────────────────────────────
const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').trim()
const baseURL = rawBaseUrl ? rawBaseUrl.replace(/\/+$/, '') : ''

const client = axios.create({
  baseURL,
  timeout: 30_000,
})

// 요청: JWT 첨부 + 만료 선제 차단
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      if (isTokenExpired(token)) {
        localStorage.removeItem('access_token')
        window.location.replace('/login')
        return Promise.reject(new Error('토큰이 만료됐습니다. 다시 로그인해 주세요.'))
      }
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (err) => Promise.reject(err),
)

// 응답: 상태 코드별 처리
client.interceptors.response.use(
  (res) => res,
  (err: AxiosError<{ detail?: string }>) => {
    const status = err.response?.status

    if (status === 401) {
      localStorage.removeItem('access_token')
      window.location.replace('/login')
      return Promise.reject(new Error('인증이 만료됐습니다. 다시 로그인해 주세요.'))
    }
    if (status === 429) {
      const msg = err.response?.data?.detail ?? '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.'
      return Promise.reject(new Error(msg))
    }
    if (status === 413) {
      return Promise.reject(new Error('파일 크기가 너무 큽니다. 20MB 이하 파일을 사용해 주세요.'))
    }
    if (status && status >= 500) {
      return Promise.reject(new Error('서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'))
    }
    if (!err.response) {
      return Promise.reject(new Error('네트워크 연결을 확인해 주세요.'))
    }

    const detail = err.response?.data?.detail
    if (detail) return Promise.reject(new Error(typeof detail === 'string' ? detail : JSON.stringify(detail)))

    return Promise.reject(err)
  },
)

export default client

// ── Auth ───────────────────────────────────────────────────────
export const register = (email: string, password: string, nickname?: string) =>
  client.post('/auth/register', { email, password, nickname })

export const login = (email: string, password: string) =>
  client.post('/auth/login', { email, password })

export const getMe = () => client.get('/auth/me')

// ── Analysis ───────────────────────────────────────────────────
export type AnalysisType = 'skin' | 'scalp' | 'lesion'

export const analyze = (type: AnalysisType, file: Blob, trackId?: number) => {
  const form = new FormData()
  form.append('file', file, 'image.jpg')
  const params = trackId != null ? { track_id: trackId } : {}
  return client.post(`/analysis/${type}`, form, {
    params,
    timeout: 90_000, // AI 분석은 최대 90초
  })
}

// ── Records ────────────────────────────────────────────────────
export const listRecords = (analysisType?: AnalysisType, limit = 10, offset = 0) =>
  client.get('/records/', { params: { analysis_type: analysisType, limit, offset } })

export const getRecord = (id: number) => client.get(`/records/${id}`)

export const createLesionTrack = (trackName: string) =>
  client.post('/records/lesion-tracks', { track_name: trackName })

export const listLesionTracks = () => client.get('/records/lesion-tracks')

export const getLesionTrackHistory = (trackId: number) =>
  client.get(`/records/lesion-tracks/${trackId}`)

// ── Health ─────────────────────────────────────────────────────
export const checkHealth = () => client.get('/health', { timeout: 5_000 })
