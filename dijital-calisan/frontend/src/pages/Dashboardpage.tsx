import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, MessageSquare, FolderOpen, Users, Upload, FolderPlus, UserPlus, BarChart2, Clock } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { chatApi } from '../api/chatApi'
import { documentApi, DocumentCategory, DocumentDto } from '../api/documentApi'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { PieChart, Pie, Cell } from 'recharts'

const PIE_COLORS = ['#E85D04', '#FFA500', '#FFD580', '#FFECC2', '#D4D4D4']

const CATEGORIES: Array<{ value: DocumentCategory; label: string }> = [
    { value: 'hr', label: 'İnsan Kaynakları' },
    { value: 'finance', label: 'Finans' },
    { value: 'legal', label: 'Hukuk' },
    { value: 'sales', label: 'Satış' },
    { value: 'technical', label: 'Teknik Dokümanlar' },
    { value: 'customer', label: 'Müşteri Bilgileri' },
    { value: 'training', label: 'Eğitim Dokümanları' },
    { value: 'faq', label: 'Sık Sorulan Sorular' },
    { value: 'meeting_note', label: 'Toplantı ve Kararlar' },
    { value: 'procedure', label: 'Operasyon' },
    { value: 'other', label: 'Diğer' },
]

interface Analytics {
    total_documents: number
    total_questions: number
    active_users: number
    category_count: number
    daily_questions: { date: string; count: number }[]
}

interface PieItem { name: string; value: number; color: string }

function timeAgo(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime()
    const m = Math.floor(diff / 60000)
    if (m < 60) return `${m} dk önce`
    const h = Math.floor(m / 60)
    if (h < 24) return `${h} saat önce`
    return `${Math.floor(h / 24)} gün önce`
}

export default function DashboardPage() {
    const { user } = useAuth()
    const navigate = useNavigate()
    const [data, setData] = useState<Analytics | null>(null)
    const [pieData, setPieData] = useState<PieItem[]>([])
    const [recentDocs, setRecentDocs] = useState<DocumentDto[]>([])
    const [recentChats, setRecentChats] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [aiInput, setAiInput] = useState('')
    const [searchInput, setSearchInput] = useState('')

    useEffect(() => {
        const fetchAll = async () => {
            setLoading(true)
            try {
                const [analyticsRes, docsRes, chatsRes] = await Promise.allSettled([
                    chatApi.analytics(),
                    documentApi.list({ page_size: 4 }),
                    chatApi.history(),
                ])
                if (analyticsRes.status === 'fulfilled') setData(analyticsRes.value.data)
                if (docsRes.status === 'fulfilled') setRecentDocs(docsRes.value.data.items)
                if (chatsRes.status === 'fulfilled') setRecentChats((chatsRes.value.data?.items ?? chatsRes.value.data ?? []).slice(0, 4))

                const counts = await Promise.all(
                    CATEGORIES.map(cat =>
                        documentApi.list({ category: cat.value, page_size: 1 })
                            .then(r => ({ name: cat.label, value: r.data.total, color: '' }))
                            .catch(() => ({ name: cat.label, value: 0, color: '' }))
                    )
                )
                setPieData(counts.filter(c => c.value > 0).map((c, i) => ({ ...c, color: PIE_COLORS[i % PIE_COLORS.length] })))
            } finally {
                setLoading(false)
            }
        }
        void fetchAll()
    }, [])

    const categoryCount = pieData.filter(p => p.value > 0).length

    const stats = [
        { label: 'Toplam Belge', value: loading ? '—' : String(data?.total_documents ?? 0), icon: FileText, bg: '#FFF0E6', color: '#E85D04' },
        { label: 'Soru Cevap', value: loading ? '—' : String(data?.total_questions ?? 0), icon: MessageSquare, bg: '#EEF2FF', color: '#6366F1' },
        { label: 'Kategoriler', value: loading ? '—' : String(categoryCount), icon: FolderOpen, bg: '#ECFDF5', color: '#10B981' },
        { label: 'Aktif Kullanıcı', value: loading ? '—' : String(data?.active_users ?? 0), icon: Users, bg: '#FFF7ED', color: '#F59E0B' },
    ]

    const chartData = data?.daily_questions?.map(d => ({
        gun: new Date(d.date + 'T00:00:00').toLocaleDateString('tr-TR', { weekday: 'short' }),
        soru: d.count,
    })) ?? []

    const quickActions = [
        { icon: Upload, label: 'Belge Yükle', onClick: () => navigate('/documents'), color: '#E85D04', bg: '#FFF0E6' },
        { icon: FolderPlus, label: 'Kategoriler', onClick: () => navigate('/categories'), color: '#6366F1', bg: '#EEF2FF' },
        { icon: UserPlus, label: 'Kullanıcılar', onClick: () => navigate('/users'), color: '#10B981', bg: '#ECFDF5' },
        { icon: BarChart2, label: 'Raporlar', onClick: () => navigate('/reports'), color: '#F59E0B', bg: '#FFF7ED' },
    ]

    const handleAiSubmit = () => {
        if (!aiInput.trim()) return
        navigate(`/chat?q=${encodeURIComponent(aiInput.trim())}`)
    }

    const handleSearch = () => {
        if (!searchInput.trim()) return
        navigate(`/documents?search=${encodeURIComponent(searchInput.trim())}`)
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
                        <p className="text-gray-500 text-sm mt-0.5">Akıllı asistanınız OfficeIQ ile işlerinizi kolaylaştırın.</p>
                    </div>
                    <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-4 py-2.5 w-64">
                        <span className="text-gray-400 text-sm">🔍</span>
                        <input
                            value={searchInput}
                            onChange={e => setSearchInput(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleSearch()}
                            placeholder="Belgelerde ara..."
                            className="flex-1 text-sm bg-transparent outline-none text-gray-600"
                        />
                        <span
                            onClick={handleSearch}
                            className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded cursor-pointer hover:bg-orange-100 hover:text-[#E85D04]"
                        >
                            ⌘K
                        </span>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-4 gap-4 mb-6">
                    {stats.map(({ label, value, icon: Icon, bg, color }) => (
                        <div key={label} className="bg-white rounded-2xl p-4 border border-gray-100 hover:shadow-md transition-shadow">
                            <div className="flex items-center justify-between mb-3">
                                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: bg }}>
                                    <Icon size={18} style={{ color }} />
                                </div>
                            </div>
                            <p className="text-2xl font-bold text-gray-800">{value}</p>
                            <p className="text-xs text-gray-500 mt-0.5">{label}</p>
                        </div>
                    ))}
                </div>

                {/* Charts */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-white rounded-2xl p-5 border border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                            <p className="font-semibold text-gray-800 text-sm">Soru İstatistikleri</p>
                            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-lg">Bu Hafta</span>
                        </div>
                        {loading ? (
                            <div className="h-40 flex items-center justify-center text-gray-300 text-sm">Yükleniyor...</div>
                        ) : chartData.length === 0 ? (
                            <div className="h-40 flex items-center justify-center text-gray-300 text-sm">Henüz veri yok</div>
                        ) : (
                            <ResponsiveContainer width="100%" height={150}>
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="colorSoru" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#E85D04" stopOpacity={0.15} />
                                            <stop offset="95%" stopColor="#E85D04" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="gun" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                                    <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                                    <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }} />
                                    <Area type="monotone" dataKey="soru" stroke="#E85D04" strokeWidth={2.5} fill="url(#colorSoru)" dot={{ fill: '#E85D04', r: 4, strokeWidth: 2, stroke: '#fff' }} />
                                </AreaChart>
                            </ResponsiveContainer>
                        )}
                    </div>

                    <div className="bg-white rounded-2xl p-5 border border-gray-100">
                        <p className="font-semibold text-gray-800 text-sm mb-4">Kategorilere Göre Belgeler</p>
                        {loading ? (
                            <div className="h-40 flex items-center justify-center text-gray-300 text-sm">Yükleniyor...</div>
                        ) : pieData.length === 0 ? (
                            <div className="h-40 flex items-center justify-center text-gray-300 text-sm">Henüz belge yok</div>
                        ) : (
                            <div className="flex items-center gap-4">
                                <PieChart width={130} height={130}>
                                    <Pie data={pieData} cx={60} cy={60} innerRadius={38} outerRadius={60} dataKey="value" strokeWidth={0}>
                                        {pieData.map((_, i) => <Cell key={i} fill={pieData[i].color} />)}
                                    </Pie>
                                </PieChart>
                                <div className="space-y-2 flex-1">
                                    <p className="text-xl font-bold text-gray-800">{data?.total_documents ?? 0}</p>
                                    <p className="text-xs text-gray-400 mb-2">Toplam belge</p>
                                    {pieData.map(item => (
                                        <div key={item.name} className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: item.color }} />
                                            <span className="text-xs text-gray-600 truncate">{item.name}</span>
                                            <span className="text-xs font-medium text-gray-700 ml-auto">{item.value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Alt kısım */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white rounded-2xl p-5 border border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                            <p className="font-semibold text-gray-800 text-sm">Son Eklenen Belgeler</p>
                            <button onClick={() => navigate('/documents')} className="text-xs text-[#E85D04] font-medium hover:underline">Tümünü Gör</button>
                        </div>
                        {loading ? (
                            <p className="text-xs text-gray-300 text-center py-4">Yükleniyor...</p>
                        ) : recentDocs.length === 0 ? (
                            <div className="text-center py-6">
                                <FileText size={24} className="text-gray-200 mx-auto mb-2" />
                                <p className="text-xs text-gray-400">Henüz belge yok</p>
                                <button onClick={() => navigate('/documents')} className="mt-2 text-xs text-[#E85D04] hover:underline">İlk belgeyi yükle</button>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {recentDocs.map(doc => (
                                    <div key={doc.id} className="flex items-center gap-3">
                                        <div className="w-8 h-8 bg-orange-50 rounded-lg flex items-center justify-center flex-shrink-0">
                                            <FileText size={14} className="text-[#E85D04]" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-gray-800 truncate font-medium">{doc.display_name}</p>
                                            <p className="text-xs text-gray-400">{CATEGORIES.find(c => c.value === doc.category)?.label}</p>
                                        </div>
                                        <p className="text-xs text-gray-400 whitespace-nowrap flex items-center gap-1">
                                            <Clock size={10} />{timeAgo(doc.created_at)}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="bg-white rounded-2xl p-5 border border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                            <p className="font-semibold text-gray-800 text-sm">Son Sorular</p>
                            <button onClick={() => navigate('/chat')} className="text-xs text-[#E85D04] font-medium hover:underline">Sohbete Git</button>
                        </div>
                        {loading ? (
                            <p className="text-xs text-gray-300 text-center py-4">Yükleniyor...</p>
                        ) : recentChats.length === 0 ? (
                            <div className="text-center py-6">
                                <MessageSquare size={24} className="text-gray-200 mx-auto mb-2" />
                                <p className="text-xs text-gray-400">Henüz soru sorulmadı</p>
                                <button onClick={() => navigate('/chat')} className="mt-2 text-xs text-[#E85D04] hover:underline">İlk soruyu sor</button>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {recentChats.map((chat, i) => (
                                    <div key={chat.id ?? i} className="flex items-start gap-3 cursor-pointer group" onClick={() => navigate('/chat')}>
                                        <div className="w-8 h-8 bg-indigo-50 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                                            <MessageSquare size={14} className="text-indigo-500" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-gray-800 truncate font-medium group-hover:text-[#E85D04] transition-colors">
                                                {chat.title ?? chat.first_message ?? 'Sohbet'}
                                            </p>
                                            <p className="text-xs text-gray-400">{chat.message_count ?? ''} mesaj</p>
                                        </div>
                                        <p className="text-xs text-gray-400 whitespace-nowrap flex items-center gap-1">
                                            <Clock size={10} />{timeAgo(chat.updated_at ?? chat.created_at)}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Right panel */}
            <div className="w-72 bg-white border-l border-gray-100 p-5 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                    <p className="font-semibold text-gray-800 text-sm">AI Asistan</p>
                    <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                        <span className="text-xs text-green-600">Çevrimiçi</span>
                    </div>
                </div>

                <p className="text-sm text-gray-500 mb-3">Merhaba! Size nasıl yardımcı olabilirim?</p>

                <div className="flex gap-2 mb-4">
                    <input
                        value={aiInput}
                        onChange={e => setAiInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleAiSubmit()}
                        placeholder="Sorunuzu yazın..."
                        className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#E85D04] focus:border-transparent"
                    />
                    <button onClick={handleAiSubmit} className="w-9 h-9 bg-[#E85D04] rounded-xl flex items-center justify-center text-white hover:bg-[#C44D00] transition-colors">
                        →
                    </button>
                </div>

                <div className="space-y-2 mb-6">
                    {['Yıllık izin hakkım kaç gün?', 'Masraf beyanı nasıl yapılır?', 'Şirket politikası nedir?'].map(q => (
                        <button key={q} onClick={() => navigate(`/chat?q=${encodeURIComponent(q)}`)}
                            className="w-full text-left text-xs text-gray-500 bg-gray-50 hover:bg-orange-50 hover:text-[#E85D04] px-3 py-2 rounded-lg transition-colors">
                            {q}
                        </button>
                    ))}
                </div>

                <div className="flex-1" />

                <div>
                    <p className="font-semibold text-gray-800 text-sm mb-3">Hızlı İşlemler</p>
                    <div className="grid grid-cols-2 gap-2">
                        {quickActions.map(({ icon: Icon, label, onClick, color, bg }) => (
                            <button key={label} onClick={onClick}
                                className="flex flex-col items-center gap-2 p-3 rounded-xl border border-gray-100 hover:shadow-sm transition-all"
                                style={{ background: bg + '40' }}>
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: bg }}>
                                    <Icon size={16} style={{ color }} />
                                </div>
                                <span className="text-xs text-gray-600 text-center">{label}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}