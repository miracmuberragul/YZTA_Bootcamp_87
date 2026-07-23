import { useCallback, useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { Download, FileText, FolderOpen, RefreshCw, Trash2, Upload } from 'lucide-react'
import { DocumentCategory, DocumentDto, DocumentStatus, documentApi } from '../api/documentApi'
import { useAuth } from '../hooks/useAuth'

const CATEGORIES: Array<{ value: DocumentCategory; label: string }> = [
  { value: 'procedure', label: 'Prosedür' },
  { value: 'contract', label: 'Sözleşme/Teklif' },
  { value: 'onboarding', label: 'Onboarding' },
  { value: 'meeting_note', label: 'Toplantı Notu' },
  { value: 'other', label: 'Diğer' },
]

const STATUS_LABELS: Record<DocumentStatus, string> = {
  uploading: 'Yükleniyor', uploaded: 'Kuyruk bekliyor', queued: 'Kuyrukta', processing: 'İşleniyor',
  processed: 'Hazır', failed: 'Başarısız', deleting: 'Siliniyor',
}

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) return error.response?.data?.detail ?? fallback
  return fallback
}

export default function DocumentsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const [docs, setDocs] = useState<DocumentDto[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [category, setCategory] = useState<DocumentCategory>('procedure')
  const [statusFilter, setStatusFilter] = useState<DocumentStatus | ''>('')
  const [categoryFilter, setCategoryFilter] = useState<DocumentCategory | ''>('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [total, setTotal] = useState(0)
  const [error, setError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const fetchDocs = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const response = await documentApi.list({
        page,
        page_size: 20,
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
      })
      setDocs(response.data.items)
      setTotalPages(response.data.total_pages)
      setTotal(response.data.total)
    } catch (error) {
      setError(errorMessage(error, 'Belgeler yüklenemedi.'))
    } finally {
      setLoading(false)
    }
  }, [categoryFilter, page, statusFilter])

  useEffect(() => { void fetchDocs() }, [fetchDocs])

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      await documentApi.upload(file, category)
      await fetchDocs()
    } catch (error) {
      setError(errorMessage(error, 'Yükleme başarısız.'))
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const handleDelete = async (document: DocumentDto) => {
    if (!window.confirm(`“${document.display_name}” dokümanını silmek istiyor musunuz?`)) return
    try {
      await documentApi.delete(document.id)
      await fetchDocs()
    } catch (error) {
      setError(errorMessage(error, 'Silme işlemi tamamlanamadı.'))
    }
  }

  const handleRetry = async (id: string) => {
    try {
      await documentApi.retry(id)
      await fetchDocs()
    } catch (error) {
      setError(errorMessage(error, 'Doküman tekrar kuyruğa alınamadı.'))
    }
  }

  const handleDownload = async (document: DocumentDto) => {
    try {
      const response = await documentApi.download(document.id)
      const url = URL.createObjectURL(response.data)
      const link = window.document.createElement('a')
      link.href = url
      link.download = document.original_filename
      link.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      setError(errorMessage(error, 'Doküman indirilemedi.'))
    }
  }

  return (
    <div className="p-6 overflow-y-auto h-full">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-800">Belgelerim</h1>
        <p className="text-gray-500 text-sm mt-0.5">Şirket dokümanlarınızı güvenle yükleyin ve işlenme durumunu takip edin.</p>
      </div>

      {isAdmin ? <div className="bg-white rounded-xl border border-dashed border-gray-300 p-8 mb-6 text-center">
        <Upload size={32} className="text-[#E85D04] mx-auto mb-3" />
        <p className="text-gray-700 font-medium mb-1">Belge Yükle</p>
        <p className="text-gray-400 text-sm mb-4">Metin tabanlı PDF, DOCX veya UTF-8 TXT — en fazla 15 MB</p>
        <div className="flex items-center justify-center gap-3">
          <select value={category} onChange={event => setCategory(event.target.value as DocumentCategory)} className="border border-gray-200 rounded-lg px-3 py-2 text-sm">
            {CATEGORIES.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
          <button onClick={() => fileRef.current?.click()} disabled={uploading} className="bg-[#E85D04] hover:bg-[#C44D00] text-white text-sm px-4 py-2 rounded-lg disabled:opacity-60">
            {uploading ? 'Yükleniyor…' : 'Dosya Seç'}
          </button>
          <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={handleUpload} />
        </div>
        {error && <p role="alert" className="text-red-500 text-sm mt-3">{error}</p>}
      </div> : (
        <div className="bg-blue-50 border border-blue-100 text-blue-700 rounded-xl px-4 py-3 mb-6 text-sm">
          Dokümanları görüntüleyebilirsiniz. Yükleme, tekrar deneme ve silme işlemleri yalnızca admin kullanıcılar tarafından yapılabilir.
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-100">
        <div className="flex items-center justify-between gap-4 px-4 py-3 border-b border-gray-100">
          <p className="font-medium text-gray-800 text-sm">Belgeler ({total})</p>
          <div className="flex items-center gap-2">
            <select value={categoryFilter} onChange={event => { setCategoryFilter(event.target.value as DocumentCategory | ''); setPage(1) }} className="border border-gray-200 rounded-lg px-2 py-1.5 text-xs">
              <option value="">Tüm kategoriler</option>
              {CATEGORIES.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
            <select value={statusFilter} onChange={event => { setStatusFilter(event.target.value as DocumentStatus | ''); setPage(1) }} className="border border-gray-200 rounded-lg px-2 py-1.5 text-xs">
              <option value="">Tüm durumlar</option>
              {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
            <button onClick={() => void fetchDocs()} className="p-1.5 text-[#E85D04]" aria-label="Belgeleri yenile"><RefreshCw size={15} /></button>
          </div>
        </div>

        {loading ? <div className="p-8 text-center text-gray-400 text-sm">Yükleniyor…</div> : docs.length === 0 ? (
          <div className="p-8 text-center"><FolderOpen size={32} className="text-gray-300 mx-auto mb-2" /><p className="text-gray-400 text-sm">Bu filtrede doküman bulunamadı.</p></div>
        ) : <div className="divide-y divide-gray-50">{docs.map(doc => (
          <div key={doc.id} className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50">
            <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center"><FileText size={16} className="text-[#E85D04]" /></div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">{doc.display_name}</p>
              <p className="text-xs text-gray-400">{CATEGORIES.find(item => item.value === doc.category)?.label} · {STATUS_LABELS[doc.status]} · {(doc.file_size_bytes / 1024).toFixed(0)} KB</p>
              {doc.processing_error_message && <p className="text-xs text-red-500 mt-0.5">{doc.processing_error_message}</p>}
            </div>
            <p className="text-xs text-gray-400 whitespace-nowrap">{new Date(doc.created_at).toLocaleDateString('tr-TR')}</p>
            {isAdmin && (doc.status === 'failed' || doc.status === 'uploaded') && <button onClick={() => void handleRetry(doc.id)} className="p-1.5 hover:bg-orange-50 rounded-lg" aria-label="Tekrar dene"><RefreshCw size={14} className="text-orange-500" /></button>}
            <button onClick={() => void handleDownload(doc)} className="p-1.5 hover:bg-gray-100 rounded-lg" aria-label="İndir"><Download size={14} className="text-gray-500" /></button>
            {isAdmin && <button onClick={() => void handleDelete(doc)} className="p-1.5 hover:bg-red-50 rounded-lg" aria-label="Sil"><Trash2 size={14} className="text-red-400" /></button>}
          </div>
        ))}</div>}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 text-sm">
            <button disabled={page === 1} onClick={() => setPage(current => current - 1)} className="text-[#E85D04] disabled:text-gray-300">Önceki</button>
            <span className="text-gray-500">{page} / {totalPages}</span>
            <button disabled={page === totalPages} onClick={() => setPage(current => current + 1)} className="text-[#E85D04] disabled:text-gray-300">Sonraki</button>
          </div>
        )}
      </div>
    </div>
  )
}
