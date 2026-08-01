import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1/chat' })
const analyticsApi = axios.create({ baseURL: '/api/v1' })

const authHeader = () => ({
    Authorization: `Bearer ${localStorage.getItem('token')}`,
})

export const chatApi = {
    ask: (question: string, conversation_id?: string) =>
        api.post('/ask', { question, conversation_id }, { headers: authHeader() }),

    history: () => api.get('/conversations', { headers: authHeader() }),

    analytics: () => analyticsApi.get('/analytics/summary', { headers: authHeader() }),
}