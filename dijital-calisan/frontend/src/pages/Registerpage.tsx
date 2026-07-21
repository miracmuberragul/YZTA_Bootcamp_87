import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi } from '../api/authApi'

export default function RegisterPage() {
    const navigate = useNavigate()
    const [form, setForm] = useState({
        company_name: '',
        company_slug: '',
        full_name: '',
        email: '',
        password: '',
    })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            await authApi.register(form)
            navigate('/login')
        } catch (err: any) {
            setError(err.response?.data?.detail ?? 'Kayıt başarısız.')
        } finally {
            setLoading(false)
        }
    }

    const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
        setForm(prev => ({ ...prev, [field]: e.target.value }))

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center py-8">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 bg-[#E85D04] rounded-xl flex items-center justify-center">
                            <span className="text-white font-bold">O</span>
                        </div>
                        <span className="text-2xl font-bold text-gray-800">OfficeIQ</span>
                    </div>
                    <p className="text-gray-500 text-sm">AI Destekli Kurumsal Bilgi Asistanı</p>
                </div>

                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
                    <h1 className="text-xl font-semibold text-gray-800 mb-6">Hesap Oluştur</h1>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Şirket Adı</label>
                            <input
                                type="text"
                                placeholder="TechNova Danışmanlık"
                                value={form.company_name}
                                onChange={set('company_name')}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#E85D04] focus:border-transparent"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Şirket Kodu</label>
                            <input
                                type="text"
                                placeholder="technova"
                                value={form.company_slug}
                                onChange={set('company_slug')}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#E85D04] focus:border-transparent"
                                required
                            />
                            <p className="text-xs text-gray-400 mt-1">Küçük harf ve tire kullanın. Giriş yaparken bu kodu kullanacaksınız.</p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Ad Soyad</label>
                            <input
                                type="text"
                                placeholder="Adınız Soyadınız"
                                value={form.full_name}
                                onChange={set('full_name')}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#E85D04] focus:border-transparent"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">E-posta</label>
                            <input
                                type="email"
                                placeholder="ornek@sirket.com"
                                value={form.email}
                                onChange={set('email')}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#E85D04] focus:border-transparent"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Şifre</label>
                            <input
                                type="password"
                                placeholder="En az 8 karakter"
                                value={form.password}
                                onChange={set('password')}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#E85D04] focus:border-transparent"
                                required
                                minLength={8}
                            />
                        </div>

                        {error && <p className="text-red-500 text-sm">{error}</p>}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-[#E85D04] hover:bg-[#C44D00] text-white font-medium py-2.5 rounded-lg text-sm transition-colors disabled:opacity-60"
                        >
                            {loading ? 'Kaydediliyor...' : 'Kayıt Ol'}
                        </button>

                        <p className="text-center text-sm text-gray-500">
                            Zaten hesabınız var mı?{' '}
                            <Link to="/login" className="text-[#E85D04] font-medium hover:underline">
                                Giriş Yap
                            </Link>
                        </p>
                    </form>
                </div>
            </div>
        </div>
    )
}