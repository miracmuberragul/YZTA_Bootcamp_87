import axios from 'axios'

const api = axios.create({ baseURL: '/auth' })

export const authApi = {
    register: (data: {
        company_name: string
        company_slug: string
        full_name: string
        email: string
        password: string
    }) => api.post('/register', data),

    login: (data: {
        email: string
        password: string
        company_slug: string
    }) => api.post('/login', data),

    me: (token: string) =>
        api.get('/me', {
            headers: { Authorization: `Bearer ${token}` },
        }),
}