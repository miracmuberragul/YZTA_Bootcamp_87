import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, MessageSquare, FolderOpen, Users, Upload, FolderPlus, UserPlus, BarChart2 } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { chatApi } from '../api/chatApi'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { PieChart, Pie, Cell } from 'recharts'


const PIE_COLORS = ['#E85D04', '#FFA500', '#FFD580', '#FFECC2', '#D4D4D4']

interface Analytics {
    total_documents: number
    processed_documents: number
    total_questions: number
    questions_this_week: number
    active_users: number
    total_categories: number
    daily_questions: { day: string; count: number }[]
    category_distribution: { name: string; count: number }[]
}

export default function DashboardPage() {
    const { user } = useAuth()
    const navigate = useNavigate()
    const [data, setData] = useState<Analytics | null>(null)
    const [loading, setLoading] = useState(true)
    const [aiInput, setAiInput] = useState('')

    useEffect(() => {
        chatApi.analytics()
            .then(res => setData(res.data))
            .catch(() => setData(null))
            .finally(() => setLoading(false))
    }, [])

    const stats = [
        { label: 'Toplam Belge', value: loading ? '—' : String(data?.total_documents ?? 0), icon: FileText },
        { label: 'Soru Cevap', value: loading ? '—' : String(data?.total_questions ?? 0), icon: MessageSquare },
        { label: 'Kategoriler', value: loading ? '—' : String(data?.total_categories ?? 0), icon: FolderOpen },
        { label: 'Aktif Kullanıcı', value: loading ? '—' : String(data?.active_users ?? 0), icon: Users },
    ]

    const chartData = data?.daily_questions?.map(d => ({
        gun: new Date(d.day + 'T00:00:00').toLocaleDateString('tr-TR', { weekday: 'short' }),
        soru: d.count,
    })) ?? []

    const pieData = data?.category_distribution?.map((c, i) => ({
        name: c.name,
        value: c.count,
        color: PIE_COLORS[i % PIE_COLORS.length],
    })) ?? []

    const totalDocs = data?.total_documents ?? 0

    const quickActions = [
        { icon: Upload, label: 'Belge Yükle', onClick: () => navigate('/documents') },
        { icon: FolderPlus, label: 'Yeni Kategori', onClick: () => navigate('/categories') },
        { icon: UserPlus, label: 'Kullanıcı Davet Et', onClick: () => navigate('/users') },
        { icon: BarChart2, label: 'Raporları Görüntüle', onClick: () => navigate('/reports') },
    ]

    const handleAiSubmit = () => {
        if (!aiInput.trim()) return
        navigate(`/chat?q=${encodeURIComponent(aiInput.trim())}`)
    }

    return (
        <div className="flex h-full">
            <div className="flex-1 p-6 overflow-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-xl font-semibold text-gray-800">
                            Günaydın, {user?.full_name?.split(' ')[0] ?? 'Kullanıcı'}! 👋
                        </h1>
                        <p className="text-gray-500 text-sm mt-0.5">
                            Akıllı asistanınız OfficeIQ ile işlerinizi kolaylaştırın.
                        </p>
                    </div>
                    <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-4 py-2.5 w-64">
                        <span className="text-gray-400 text-sm">🔍</span>
                        <input
                            placeholder="Belgelerde ara..."
                            className="flex-1 text-sm bg-transparent outline-none text-gray-600"
                        />
                        <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">⌘K</span>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-4 gap-4 mb-6">
                    {stats.map(({ label, value, icon: Icon }) => (
                        <div key={label} className="bg-white rounded-xl p-4 border border-gray-100">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-gray-500 text-xs">{label}</p>
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: '#FFF0E6' }}>
                                    <Icon size={16} className="text-[#E85D04]" />
                                </div>
                            </div>
                            <p className="text-2xl font-bold text-gray-800">{value}</p>
                            <p className="text-xs mt-1 text-gray-400">Bu hafta</p>
                        </div>
                    ))}
                </div>

                {/* Charts */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white rounded-xl p-4 border border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                            <p className="font-medium text-gray-800 text-sm">Soru İstatistikleri</p>
                            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-lg">Bu Hafta</span>
                        </div>
                        {loading ? (
                            <div className="h-40 flex items-center justify-center text-gray-400 text-sm">Yükleniyor...</div>
                        ) : chartData.length === 0 ? (
                            <div className="h-40 flex items-center justify-center text-gray-400 text-sm">Henüz veri yok</div>
                        ) : (
                            <ResponsiveContainer width="100%" height={160}>
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="colorSoru" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#E85D04" stopOpacity={0.15} />
                                            <stop offset="95%" stopColor="#E85D04" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="gun" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                                    <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                                    <Tooltip />
                                    <Area type="monotone" dataKey="soru" stroke="#E85D04" strokeWidth={2} fill="url(#colorSoru)" dot={{ fill: '#E85D04', r: 4 }} />
                                </AreaChart>
                            </ResponsiveContainer>
                        )}
                    </div>

                    <div className="bg-white rounded-xl p-4 border border-gray-100">
                        <p className="font-medium text-gray-800 text-sm mb-4">Kategorilere Göre Belgeler</p>
                        {loading ? (
                            <div className="h-40 flex items-center justify-center text-gray-400 text-sm">Yükleniyor...</div>
                        ) : pieData.length === 0 ? (
                            <div className="h-40 flex items-center justify-center text-gray-400 text-sm">Henüz kategori yok</div>
                        ) : (
                            <div className="flex items-center gap-4">
                                <PieChart width={140} height={140}>
                                    <Pie data={pieData} cx={65} cy={65} innerRadius={40} outerRadius={65} dataKey="value">
                                        {pieData.map((entry, i) => (
                                            <Cell key={i} fill={entry.color} />
                                        ))}
                                    </Pie>
                                </PieChart>
                                <div className="space-y-2">
                                    <p className="text-2xl font-bold text-gray-800">{totalDocs}</p>
                                    <p className="text-xs text-gray-400">Toplam</p>
                                    {pieData.slice(0, 5).map(item => (
                                        <div key={item.name} className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: item.color }} />
                                            <span className="text-xs text-gray-600 truncate max-w-24">{item.name}</span>
                                            <span className="text-xs text-gray-400 ml-auto">{item.value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Right panel */}
            <div className="w-72 bg-white border-l border-gray-100 p-4 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                    <p className="font-semibold text-gray-800 text-sm">AI Asistan</p>
                    <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 bg-green-500 rounded-full" />
                        <span className="text-xs text-green-600">Çevrimiçi</span>
                    </div>
                </div>

                <p className="text-sm text-gray-500 mb-3">Merhaba! Size nasıl yardımcı olabilirim?</p>

                <div className="flex gap-2 mb-6">
                    <input
                        value={aiInput}
                        onChange={e => setAiInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleAiSubmit()}
                        placeholder="Sorunuzu yazın..."
                        className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#E85D04] focus:border-transparent"
                    />
                    <button
                        onClick={handleAiSubmit}
                        className="w-8 h-8 bg-[#E85D04] rounded-lg flex items-center justify-center text-white text-sm hover:bg-[#C44D00] transition-colors"
                    >
                        →
                    </button>
                </div>

                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <div className="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-3">
                            <MessageSquare size={32} className="text-[#E85D04]" />
                        </div>
                        <p className="text-xs text-gray-400">Belge yükleyin ve sorular sormaya başlayın</p>
                    </div>
                </div>

                <div>
                    <p className="font-semibold text-gray-800 text-sm mb-3">Hızlı İşlemler</p>
                    <div className="grid grid-cols-2 gap-2">
                        {quickActions.map(({ icon: Icon, label, onClick }) => (
                            <button
                                key={label}
                                onClick={onClick}
                                className="flex flex-col items-center gap-1.5 p-3 bg-gray-50 rounded-xl hover:bg-orange-50 hover:border-orange-200 border border-gray-100 transition-colors"
                            >
                                <Icon size={18} className="text-[#E85D04]" />
                                <span className="text-xs text-gray-600 text-center">{label}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}