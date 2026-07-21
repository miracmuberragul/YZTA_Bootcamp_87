import { FileText, MessageSquare, FolderOpen, Users, Upload, FolderPlus, UserPlus, BarChart2, Download, CloudUpload } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
} from 'recharts'
import { PieChart, Pie, Cell } from 'recharts'

const chartData = [
    { gun: 'Pzt', soru: 5 },
    { gun: 'Sal', soru: 22 },
    { gun: 'Çar', soru: 18 },
    { gun: 'Per', soru: 40 },
    { gun: 'Cum', soru: 62 },
    { gun: 'Cmt', soru: 20 },
    { gun: 'Paz', soru: 30 },
]

const pieData = [
    { name: 'İnsan Kaynakları', value: 70, color: '#E85D04' },
    { name: 'İK Politikaları', value: 60, color: '#FFA500' },
    { name: 'BT Politikaları', value: 50, color: '#FFD580' },
    { name: 'Finans', value: 40, color: '#FFECC2' },
    { name: 'Diğer', value: 28, color: '#F5F5F5' },
]

const recentDocs = [
    { name: 'Çalışan El Kitabı.pdf', category: 'İnsan Kaynakları', time: '2 saat önce', color: '#E85D04' },
    { name: 'İzin Politikası.pdf', category: 'İK Politikaları', time: '5 saat önce', color: '#4B6BFB' },
    { name: 'Bilgi Güvenliği Politikası.pdf', category: 'BT Politikaları', time: '1 gün önce', color: '#4B6BFB' },
    { name: 'Masraf Yönergesi.pdf', category: 'Finans', time: '2 gün önce', color: '#4B6BFB' },
]

const activities = [
    { icon: CloudUpload, text: 'Çalışan El Kitabı.pdf yüklendi', sub: 'Miraç Gül tarafından', time: '2 saat önce', color: '#E85D04' },
    { icon: MessageSquare, text: 'Yeni soru soruldu', sub: '"Uzaktan çalışma politikamız nedir?"', time: '3 saat önce', color: '#6366F1' },
    { icon: FolderPlus, text: '"İK Politikaları" kategorisi oluşturuldu', sub: 'Miraç Gül tarafından', time: '5 saat önce', color: '#E85D04' },
    { icon: Download, text: 'Masraf Yönergesi.pdf indirildi', sub: 'Ahmet Yılmaz tarafından', time: '1 gün önce', color: '#10B981' },
]

const stats = [
    { label: 'Toplam Belge', value: '248', change: '+12%', up: true, icon: FileText, color: '#E85D04' },
    { label: 'Soru Cevap', value: '156', change: '+23%', up: true, icon: MessageSquare, color: '#E85D04' },
    { label: 'Kategoriler', value: '16', change: '+5%', up: true, icon: FolderOpen, color: '#E85D04' },
    { label: 'Aktif Kullanıcı', value: '8', change: '-3%', up: false, icon: Users, color: '#E85D04' },
]

const quickActions = [
    { icon: Upload, label: 'Belge Yükle' },
    { icon: FolderPlus, label: 'Yeni Kategori' },
    { icon: UserPlus, label: 'Kullanıcı Davet Et' },
    { icon: BarChart2, label: 'Raporları Görüntüle' },
]

export default function DashboardPage() {
    const { user } = useAuth()

    return (
        <div className="flex h-full">
            {/* Main content */}
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
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-4 py-2.5 w-64">
                            <span className="text-gray-400 text-sm">🔍</span>
                            <input
                                placeholder="Belgelerde ara..."
                                className="flex-1 text-sm bg-transparent outline-none text-gray-600"
                            />
                            <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">⌘K</span>
                        </div>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-4 gap-4 mb-6">
                    {stats.map(({ label, value, change, up, icon: Icon, color }) => (
                        <div key={label} className="bg-white rounded-xl p-4 border border-gray-100">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-gray-500 text-xs">{label}</p>
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: '#FFF0E6' }}>
                                    <Icon size={16} style={{ color }} />
                                </div>
                            </div>
                            <p className="text-2xl font-bold text-gray-800">{value}</p>
                            <p className={`text-xs mt-1 ${up ? 'text-green-500' : 'text-red-500'}`}>
                                {change} Bu hafta
                            </p>
                        </div>
                    ))}
                </div>

                {/* Charts row */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                    {/* Area chart */}
                    <div className="bg-white rounded-xl p-4 border border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                            <p className="font-medium text-gray-800 text-sm">Soru İstatistikleri</p>
                            <button className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-lg">Bu Hafta ▾</button>
                        </div>
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
                    </div>

                    {/* Recent docs */}
                    <div className="bg-white rounded-xl p-4 border border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                            <p className="font-medium text-gray-800 text-sm">Son Eklenen Belgeler</p>
                            <button className="text-xs text-[#E85D04] font-medium">Tümünü Gör</button>
                        </div>
                        <div className="space-y-3">
                            {recentDocs.map(doc => (
                                <div key={doc.name} className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold" style={{ background: doc.color }}>
                                        PDF
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-800 truncate">{doc.name}</p>
                                        <p className="text-xs text-gray-400">{doc.category}</p>
                                    </div>
                                    <p className="text-xs text-gray-400 whitespace-nowrap">{doc.time}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Bottom row */}
                <div className="grid grid-cols-2 gap-4">
                    {/* Pie chart */}
                    <div className="bg-white rounded-xl p-4 border border-gray-100">
                        <p className="font-medium text-gray-800 text-sm mb-4">Kategorilere Göre Belgeler</p>
                        <div className="flex items-center gap-4">
                            <PieChart width={140} height={140}>
                                <Pie data={pieData} cx={65} cy={65} innerRadius={40} outerRadius={65} dataKey="value">
                                    {pieData.map((entry, i) => (
                                        <Cell key={i} fill={entry.color} />
                                    ))}
                                </Pie>
                            </PieChart>
                            <div className="space-y-2">
                                <p className="text-2xl font-bold text-gray-800">248</p>
                                <p className="text-xs text-gray-400">Toplam</p>
                                {pieData.map(item => (
                                    <div key={item.name} className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full" style={{ background: item.color }} />
                                        <span className="text-xs text-gray-600">{item.name}</span>
                                        <span className="text-xs text-gray-400 ml-auto">{item.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Activities */}
                    <div className="bg-white rounded-xl p-4 border border-gray-100">
                        <p className="font-medium text-gray-800 text-sm mb-4">Son Aktiviteler</p>
                        <div className="space-y-3">
                            {activities.map((act, i) => (
                                <div key={i} className="flex items-start gap-3">
                                    <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: act.color + '20' }}>
                                        <act.icon size={14} style={{ color: act.color }} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-gray-800 truncate">{act.text}</p>
                                        <p className="text-xs text-gray-400 truncate">{act.sub}</p>
                                    </div>
                                    <p className="text-xs text-gray-400 whitespace-nowrap">{act.time}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Right panel - AI Assistant */}
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
                        placeholder="Sorunuzu yazın..."
                        className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#E85D04] focus:border-transparent"
                    />
                    <button className="w-8 h-8 bg-[#E85D04] rounded-lg flex items-center justify-center text-white text-sm">
                        →
                    </button>
                </div>

                {/* Robot illustration placeholder */}
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <div className="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-3">
                            <MessageSquare size={32} className="text-[#E85D04]" />
                        </div>
                        <p className="text-xs text-gray-400">Belge yükleyin ve sorular sormaya başlayın</p>
                    </div>
                </div>

                {/* Quick actions */}
                <div>
                    <p className="font-semibold text-gray-800 text-sm mb-3">Hızlı İşlemler</p>
                    <div className="grid grid-cols-2 gap-2">
                        {quickActions.map(({ icon: Icon, label }) => (
                            <button
                                key={label}
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