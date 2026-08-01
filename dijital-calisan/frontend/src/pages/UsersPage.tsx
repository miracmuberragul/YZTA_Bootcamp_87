import { FormEvent, useEffect, useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { CompanyUser, managementApi } from '../api/managementApi'

export default function UsersPage() {
  const [users, setUsers] = useState<CompanyUser[]>([])
  const [form, setForm] = useState({full_name:'',email:'',password:'',role:'employee'})
  const [error, setError] = useState('')
  const load = () => managementApi.users().then(r => setUsers(r.data)).catch(() => setError('Kullanıcılar alınamadı.'))
  useEffect(() => { void load() }, [])
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError('')
    try { await managementApi.createUser(form); setForm({full_name:'',email:'',password:'',role:'employee'}); load() }
    catch (e:any) { setError(e.response?.data?.detail ?? 'Kullanıcı oluşturulamadı.') }
  }
  return <section className="h-full overflow-auto p-8">
    <h1 className="text-2xl font-bold">Kullanıcılar</h1>
    <p className="mt-1 text-sm text-gray-500">Yöneticiler tüm ayarlara, çalışanlar AI asistana erişir.</p>
    <form onSubmit={submit} className="my-6 grid gap-3 rounded-xl bg-white p-4 shadow-sm md:grid-cols-5">
      <input required placeholder="Ad soyad" className="rounded-lg border px-3 py-2" value={form.full_name}
        onChange={e=>setForm({...form,full_name:e.target.value})}/>
      <input required type="email" placeholder="E-posta" className="rounded-lg border px-3 py-2" value={form.email}
        onChange={e=>setForm({...form,email:e.target.value})}/>
      <input required minLength={8} type="password" placeholder="Geçici şifre" className="rounded-lg border px-3 py-2" value={form.password}
        onChange={e=>setForm({...form,password:e.target.value})}/>
      <select className="rounded-lg border px-3 py-2" value={form.role} onChange={e=>setForm({...form,role:e.target.value})}>
        <option value="employee">Çalışan</option><option value="admin">Yönetici</option>
      </select>
      <button className="flex items-center justify-center gap-2 rounded-lg bg-[#E85D04] text-white"><Plus size={17}/> Oluştur</button>
    </form>
    {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
    <div className="overflow-hidden rounded-xl bg-white shadow-sm">
      {users.map(user=><div key={user.id} className="flex items-center gap-4 border-b px-5 py-4 last:border-0">
        <div className="flex-1"><strong>{user.full_name}</strong><p className="text-sm text-gray-500">{user.email}</p></div>
        <span className="rounded-full bg-orange-50 px-3 py-1 text-xs text-[#E85D04]">{user.role==='admin'?'Yönetici':'Çalışan'}</span>
        <button onClick={()=>managementApi.updateUser(user.id,{is_active:!user.is_active}).then(load)}
          className={`rounded-full px-3 py-1 text-xs ${user.is_active?'bg-green-50 text-green-700':'bg-gray-100 text-gray-500'}`}>
          {user.is_active?'Aktif':'Pasif'}
        </button>
        <button aria-label={`${user.full_name} kullanıcısını sil`} onClick={()=>managementApi.deleteUser(user.id).then(load)}
          className="text-gray-400 hover:text-red-600"><Trash2 size={18}/></button>
      </div>)}
    </div>
  </section>
}
