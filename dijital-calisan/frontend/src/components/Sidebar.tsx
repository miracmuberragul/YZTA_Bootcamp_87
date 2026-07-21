import { NavLink, useNavigate } from 'react-router-dom'
import {
    LayoutDashboard,
    MessageSquare,
    FileText,
    FolderOpen,
    BarChart2,
    Users,
    Settings,
    LogOut,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const nav = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/chat', icon: MessageSquare, label: 'AI Asistan' },
    { to: '/documents', icon: FileText, label: 'Belgelerim' },
    { to: '/categories', icon: FolderOpen, label: 'Kategoriler' },
    { to: '/reports', icon: BarChart2, label: 'Raporlar' },
    { to: '/users', icon: Users, label: 'Kullanıcılar' },
    { to: '/settings', icon: Settings, label: 'Ayarlar' },
]

export default function Sidebar() {
    const { user, logout } = useAuth()
    const navigate = useNavigate()

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <aside className="w-56 bg-[#E85D04] flex flex-col h-screen">
            {/* Logo */}
            <div className="px-5 py-6">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                        <span className="text-[#E85D04] font-bold text-sm">O</span>
                    </div>
                    <div>
                        <p className="text-white font-bold text-sm leading-none">OfficeIQ</p>
                        <p className="text-orange-200 text-[10px] leading-none mt-0.5">AI Destekli Kurumsal Asistan</p>
                    </div>
                </div>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-3 space-y-0.5">
                {nav.map(({ to, icon: Icon, label }) => (
                    <NavLink
                        key={to}
                        to={to}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${isActive
                                ? 'bg-white text-[#E85D04] font-semibold'
                                : 'text-orange-100 hover:bg-orange-600'
                            }`
                        }
                    >
                        <Icon size={18} />
                        {label}
                    </NavLink>
                ))}
            </nav>

            {/* User */}
            <div className="px-3 pb-5">
                <div className="flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-orange-600 cursor-pointer">
                    <div className="w-8 h-8 bg-orange-300 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                        {user?.full_name?.[0] ?? 'U'}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-white text-sm font-medium truncate">{user?.full_name ?? 'Kullanıcı'}</p>
                        <p className="text-orange-200 text-xs capitalize">{user?.role === 'admin' ? 'Yönetici' : 'Personel'}</p>
                    </div>
                    <button onClick={handleLogout}>
                        <LogOut size={16} className="text-orange-200 hover:text-white" />
                    </button>
                </div>
            </div>
        </aside>
    )
}