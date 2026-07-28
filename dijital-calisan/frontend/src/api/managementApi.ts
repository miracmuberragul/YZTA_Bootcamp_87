import axios from 'axios'

const headers = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` })

export type Category = { id: string; name: string; color: string; document_count: number }
export type CompanyUser = {
  id: string; full_name: string; email: string; role: 'admin' | 'employee'; is_active: boolean
}
export type CompanySettings = {
  company_name: string; max_upload_mb: number; retrieval_limit: number
  min_similarity: number; system_prompt: string | null
}

export const managementApi = {
  categories: () => axios.get<Category[]>('/api/v1/categories', { headers: headers() }),
  createCategory: (data: { name: string; color: string }) =>
    axios.post<Category>('/api/v1/categories', data, { headers: headers() }),
  deleteCategory: (id: string) =>
    axios.delete(`/api/v1/categories/${id}`, { headers: headers() }),
  users: () => axios.get<CompanyUser[]>('/api/auth/users', { headers: headers() }),
  createUser: (data: { full_name: string; email: string; password: string; role: string }) =>
    axios.post<CompanyUser>('/api/auth/users', data, { headers: headers() }),
  updateUser: (id: string, data: Partial<CompanyUser>) =>
    axios.patch<CompanyUser>(`/api/auth/users/${id}`, data, { headers: headers() }),
  deleteUser: (id: string) => axios.delete(`/api/auth/users/${id}`, { headers: headers() }),
  settings: () => axios.get<CompanySettings>('/api/auth/settings', { headers: headers() }),
  saveSettings: (data: CompanySettings) =>
    axios.put<CompanySettings>('/api/auth/settings', data, { headers: headers() }),
  analytics: () => axios.get('/api/v1/analytics/summary', { headers: headers() }),
}
