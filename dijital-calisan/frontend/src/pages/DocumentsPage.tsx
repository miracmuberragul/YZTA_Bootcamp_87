import { useState, useRef } from 'react'
import { Upload, FileText, Trash2, FolderOpen } from 'lucide-react'
import { documentApi } from '../api/documentApi'

const CATEGORIES = ['Prosedür', 'Sözleşme/Teklif', 'Onboarding', 'Toplantı Notu', 'Diğer']

interface Doc {
  id: string
  filename: string
  category: string
  status: string
  uploaded_at: string
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Doc[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [category, setCategory] = useState(CATEGORIES[0])
  const [error, setError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const fetchDocs = async () => {
    setLoading(true)
    try {
      const res = await documentApi.list()
      setDocs(res.data.data ?? [])
    } catch {
      setError('Belgeler yüklenemedi.')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      await documentApi.upload(file, category)
      await fetchDocs()
    } catch {
      setError('Yükleme başarısız.')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await documentApi.delete(id)
      setDocs(prev => prev.filter(d => d.id !== id))
    } catch {
      setError('Silme başarısız.')
    }
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-800">Belgelerim</h1>
        <p className="text-gray-500 text-sm mt-0.5">Şirket dokümanlarınızı yükleyin ve yönetin</p>
      </div>

      {/* Upload area */}
      <div className="bg-white rounded-xl border border-dashed border-gray-300 p-8 mb-6 text-center">
        <Upload size={32} className="text-[#E85D04] mx-auto mb-3" />
        <p className="text-gray-700 font-medium mb-1">Belge Yükle</p>
        <p className="text-gray-400 text-sm mb-4">PDF, DOCX veya TXT — maks. 15 MB</p>

        <div className="flex items-center justify-center gap-3">
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#E85D04]"
          >
            {CATEGORIES.map(c => <option key={c}>{c}</option>)}
          </select>

          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="bg-[#E85D04] hover:bg-[#C44D00] text-white text-sm px-4 py-2 rounded-lg transition-colors disabled:opacity-60"
          >
            {uploading ? 'Yükleniyor...' : 'Dosya Seç'}
          </button>
          <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={handleUpload} />
        </div>

        {error && <p className="text-red-500 text-sm mt-3">{error}</p>}
      </div>

      {/* Doc list */}
      <div className="bg-white rounded-xl border border-gray-100">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
          <p className="font-medium text-gray-800 text-sm">Belgeler ({docs.length})</p>
          <button onClick={fetchDocs} className="text-xs text-[#E85D04] font-medium">Yenile</button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Yükleniyor...</div>
        ) : docs.length === 0 ? (
          <div className="p-8 text-center">
            <FolderOpen size={32} className="text-gray-300 mx-auto mb-2" />
            <p className="text-gray-400 text-sm">Henüz belge yok. İlk belgenizi yükleyin.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {docs.map(doc => (
              <div key={doc.id} className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50">
                <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                  <FileText size={16} className="text-[#E85D04]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{doc.filename}</p>
                  <p className="text-xs text-gray-400">{doc.category} · {doc.status}</p>
                </div>
                <p className="text-xs text-gray-400 whitespace-nowrap">
                  {new Date(doc.uploaded_at).toLocaleDateString('tr-TR')}
                </p>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="p-1.5 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 size={14} className="text-red-400" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}