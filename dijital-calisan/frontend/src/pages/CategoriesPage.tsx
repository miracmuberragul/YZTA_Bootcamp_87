import { FormEvent, useEffect, useState } from 'react'
import { FolderOpen, Plus, Trash2 } from 'lucide-react'
import { Category, managementApi } from '../api/managementApi'

export default function CategoriesPage() {
  const [items, setItems] = useState<Category[]>([])
  const [name, setName] = useState('')
  const [color, setColor] = useState('#E85D04')
  const [error, setError] = useState('')
  const load = () => managementApi.categories().then(r => setItems(r.data)).catch(() => setError('Kategoriler alınamadı.'))
  useEffect(() => { void load() }, [])
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError('')
    try { await managementApi.createCategory({ name, color }); setName(''); load() }
    catch (e: any) { setError(e.response?.data?.detail ?? 'Kategori oluşturulamadı.') }
  }
  return <section className="h-full overflow-auto p-8">
    <h1 className="text-2xl font-bold text-gray-900">Kategoriler</h1>
    <p className="mt-1 text-sm text-gray-500">Belgelerinizi şirketinize özel başlıklarla düzenleyin.</p>
    <form onSubmit={submit} className="my-6 flex gap-3 rounded-xl bg-white p-4 shadow-sm">
      <input value={name} onChange={e => setName(e.target.value)} required minLength={2}
        placeholder="Kategori adı" className="flex-1 rounded-lg border px-3 py-2" />
      <input type="color" value={color} onChange={e => setColor(e.target.value)}
        className="h-10 w-12 rounded border p-1" />
      <button className="flex items-center gap-2 rounded-lg bg-[#E85D04] px-4 text-white"><Plus size={17}/> Ekle</button>
    </form>
    {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map(item => <article key={item.id} className="flex items-center gap-3 rounded-xl bg-white p-5 shadow-sm">
        <span className="rounded-lg p-3" style={{backgroundColor: `${item.color}20`, color: item.color}}><FolderOpen/></span>
        <div className="flex-1"><strong>{item.name}</strong><p className="text-sm text-gray-500">{item.document_count} belge</p></div>
        <button aria-label={`${item.name} kategorisini sil`} onClick={() => managementApi.deleteCategory(item.id).then(load)}
          className="text-gray-400 hover:text-red-600"><Trash2 size={18}/></button>
      </article>)}
    </div>
  </section>
}
