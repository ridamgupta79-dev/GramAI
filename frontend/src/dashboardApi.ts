import { api } from './api'

export interface DashboardSection {
  data: Record<string, any>
  narrative?: string
  sources?: string[]
}

export interface DashboardPayload {
  report_id: string
  context: Record<string, any>
  sections: Record<string, DashboardSection>
}

export const generateDashboard = (body: {
  location: { village: string; block: string; district: string; state: string }
  sector: string
  margin_capital: number
  monthly_operating_cost?: number | null
  gender?: string | null
  language: string
}) => api.post<DashboardPayload>('/dashboard/generate', body).then(r => r.data)

export const downloadReport = async (reportId: string) => {
  const res = await api.get(`/reports/${reportId}/pdf`, {
    responseType: 'blob',
  })

  const blob = new Blob([res.data], { type: 'application/pdf' })
  const url = URL.createObjectURL(blob)

  const a = document.createElement('a')
  a.href = url
  document.body.appendChild(a)
  a.click()
  a.remove()

  URL.revokeObjectURL(url)
}

export const mentorChat = (
  question: string,
  reportId?: string,
  language = 'English'
) =>
  api.post<{ answer: string }>('/dashboard/mentor', {
    question,
    report_id: reportId ?? null,
    language,
  }).then(r => r.data)

export const applyForScheme = (
  reportId: string,
  applicantName: string,
  phone: string,
  scheme: string
) =>
  api.post<{
    application_id: string
    status: string
    message: string
  }>('/dashboard/apply', {
    report_id: reportId,
    applicant_name: applicantName,
    phone,
    scheme,
  }).then(r => r.data)