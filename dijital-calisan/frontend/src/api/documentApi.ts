import axios from 'axios'

export type DocumentCategory = 'procedure' | 'contract' | 'onboarding' | 'meeting_note' | 'other'
export type DocumentStatus = 'uploading' | 'uploaded' | 'queued' | 'processing' | 'processed' | 'failed' | 'deleting'

export interface DocumentDto {
  id: string
  original_filename: string
  display_name: string
  mime_type: string
  file_size_bytes: number
  category: DocumentCategory
  status: DocumentStatus
  processing_error_code: string | null
  processing_error_message: string | null
  created_at: string
}

export interface DocumentListDto {
  items: DocumentDto[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

const api = axios.create({ baseURL: '/api/v1/documents' })
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const documentApi = {
  list: (params?: { page?: number; page_size?: number; status?: DocumentStatus; category?: DocumentCategory }) =>
    api.get<DocumentListDto>('', { params }),

  upload: (file: File, category: DocumentCategory, displayName?: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('category', category)
    if (displayName) form.append('display_name', displayName)
    return api.post('', form)
  },

  retry: (id: string) => api.post(`/${id}/retry-ingestion`),
  delete: (id: string) => api.delete(`/${id}`),
  download: (id: string) => api.get(`/${id}/content`, { responseType: 'blob' }),
}
