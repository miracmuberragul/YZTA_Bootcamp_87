import axios from 'axios'

const api = axios.create({ baseURL: '/api/documents' })

const authHeader = () => ({
    Authorization: `Bearer ${localStorage.getItem('token')}`,
})

export const documentApi = {
    list: () => api.get('/', { headers: authHeader() }),

    upload: (file: File, category: string) => {
        const form = new FormData()
        form.append('file', file)
        form.append('category', category)
        return api.post('/upload', form, {
            headers: { ...authHeader(), 'Content-Type': 'multipart/form-data' },
        })
    },

    delete: (id: string) =>
        api.delete(`/${id}`, { headers: authHeader() }),
}