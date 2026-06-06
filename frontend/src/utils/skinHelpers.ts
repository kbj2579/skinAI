import { colors } from '../theme'

export interface SkinMetrics {
  oiliness: number
  moisture: number
  trouble: number
  sensitivity: number
}

export const TYPE_LABELS: Record<string, string> = {
  skin: '안면피부',
  lesion: '병변',
}

export const METRIC_LABELS: Record<keyof SkinMetrics, string> = {
  oiliness: '유분도',
  moisture: '수분도',
  trouble: '트러블',
  sensitivity: '민감도',
}

export const scoreColor = (score: number) => {
  if (score >= 0.7) return colors.danger
  if (score >= 0.4) return colors.warning
  return colors.success
}

export const metricColor = (key: string, value: number) => {
  if (key === 'moisture') {
    if (value >= 60) return colors.success
    if (value >= 40) return colors.warning
    return colors.danger
  }
  if (value <= 30) return colors.success
  if (value <= 60) return colors.warning
  return colors.danger
}
