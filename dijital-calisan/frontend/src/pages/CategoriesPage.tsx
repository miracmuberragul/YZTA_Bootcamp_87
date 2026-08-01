import { useEffect, useRef, useState } from 'react'
import { FolderOpen, Upload, X, FileText } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Category, managementApi } from '../api/managementApi'
import { documentApi, DocumentCategory, DocumentDto } from '../api/documentApi'

const ENUM_CATEGORIES: Array<{ value: DocumentCategory; label: string; color: string }> = [
  { value: 'hr', label: 'İnsan Kaynakları', color: '#E85D04' },
  { value: 'finance', label: 'Finans', color: '#3B82F6' },
  { value: 'legal', label: 'Hukuk', color: '#10B981' },
  { value: 'sales', label: 'Satış', color: '#8B5CF6' },
  { value: 'technical', label: 'Teknik Dokümanlar', color: '#F59E0B' },
  { value: 'customer', label: 'Müşteri Bilgileri', color: '#EC4899' },
  { value: 'training', label: 'Eğitim Dokümanları', color: '#14B8A6' },
  { value: 'faq', label: 'Sık Sorulan Sorular', color: '#6366F1' },
  { value: 'meeting_note', label: 'Toplantı ve Kararlar', color: '#84CC16' },
  { value: 'procedure', label: 'Operasyon', color: '#F97316' },
  { value: 'other', label: 'Diğer', color: '#6B7280' },
]

interface EnumCategoryWithCount {
  value: DocumentCategory
  label: string
  color: string
  count: number
}

export default function CategoriesPage() {
  const navigate = useNavigate()
  const [enumItems, setEnumItems] = useState<EnumCategoryWithCount[]>([])
  const [dynamicItems, setDynamicItems] = useState<Category[]>([])
  const [selectedEnum, setSelectedEnum] = useState<EnumCategoryWithCount | null>(null)
  const [selectedDynamic, setSelectedDynamic] = useState<Category | null>(null)
  const [docs, setDocs] = useState<DocumentDto[]>([])
  const [docsLoading, setDocsLoading] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const uploadTargetRef = useRef<DocumentCategory | null>(null)

  const loadEnumCounts = async () => {
    const counts = await Promise.all(
      ENUM_CATEGORIES.map(cat =>
        documentApi.list({ category: cat.value, page_size: 1 })
          .then(r => ({ ...cat, count: r.data.total }))
          .catch(() => ({ ...cat, count: 0 }))
      )
    )
    setEnumItems(counts)
  }

  useEffect(() => {
    void loadEnumCounts()
    managementApi.categories().then(r => setDynamicItems(r.data)).catch(() => { })
  }, [])

  const openEnumCategory = async (item: EnumCategoryWithCount) => {
    setSelectedEnum(item)
    setSelectedDynamic(null)
    setDocsLoading(true)
    try {
      const res = await documentApi.list({ category: item.value, page_size: 50 })
      setDocs(res.data.items)
    } catch {
      setDocs([])
    } finally {
      setDocsLoading(false)
    }
  }

  const close = () => {
    setSelectedEnum(null)
    setSelectedDynamic(null)
    setDocs([])
  }

  const handleUploadClick = (category: DocumentCategory) => {
    uploadTargetRef.current = category
    fileRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    const cat = uploadTargetRef.current
    if (!file || !cat) return
    setError('')
    try {
      await documentApi.upload(file, cat)
      await loadEnumCounts()
      if (selectedEnum?.value === cat) {
        const res = await documentApi.list({ category: cat, page_size: 50 })
        setDocs(res.data.items)
      }
    } catch (e: any) {
      setError(e.response?.data?.detail ?? 'Yükleme başarısız.')
    } finally {
      uploadTargetRef.current = null
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const activeColor = selectedEnum?.color ?? '#E85D04'
  const activeLabel = selectedEnum?.label ?? selectedDynamic?.name ?? ''

  return (
    <section className="h-full overflow-auto p-8">
      <h1 className="text-2xl font-bold text-gray-900">Kategoriler</h1>
      <p className="mt-1 text-sm text-gray-500">Kategoriye tıklayarak belgelerini görüntüleyin.</p>

      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.docx,.txt"
        className="hidden"
        onChange={handleFileChange}
      />

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {/* Kategori detay paneli */}
      {(selectedEnum || selectedDynamic) && (
        <div className="mt-6 rounded-xl bg-white shadow-sm border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="rounded-lg p-2" style={{ backgroundColor: `${activeColor}20`, color: activeColor }}>
                <FolderOpen size={20} />
              </span>
              <div>
                <h2 className="font-semibold text-gray-800">{activeLabel}</h2>
                <p className="text-xs text-gray-400">{docs.length} belge</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {selectedEnum && (
                <button
                  onClick={() => handleUploadClick(selectedEnum.value)}
                  className="flex items-center gap-1.5 text-xs bg-[#E85D04] text-white px-3 py-1.5 rounded-lg hover:bg-[#C44D00] transition-colors"
                >
                  <Upload size={13} /> Belge Yükle
                </button>
              )}
              <button onClick={close} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg">
                <X size={18} />
              </button>
            </div>
          </div>

          {docsLoading ? (
            <p className="text-sm text-gray-400 text-center py-6">Yükleniyor...</p>
          ) : docs.length === 0 ? (
            <div className="text-center py-8">
              <FolderOpen size={28} className="text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-400">Bu kategoride henüz belge yok.</p>
              {selectedEnum && (
                <button
                  onClick={() => handleUploadClick(selectedEnum.value)}
                  className="mt-3 text-xs text-[#E85D04] hover:underline"
                >
                  İlk belgeyi yükle
                </button>
              )}
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {docs.map(doc => (
                <div key={doc.id} className="flex items-center gap-3 py-3">
                  <div className="w-7 h-7 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FileText size={14} className="text-[#E85D04]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{doc.display_name}</p>
                    <p className="text-xs text-gray-400">{(doc.file_size_bytes / 1024).toFixed(0)} KB · {doc.status === 'processed' ? 'Hazır' : doc.status}</p>
                  </div>
                  <p className="text-xs text-gray-400 whitespace-nowrap">
                    {new Date(doc.created_at).toLocaleDateString('tr-TR')}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Sistem kategorileri */}
      <div className="mt-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Sistem Kategorileri</h2>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {enumItems.map(item => (
            <article
              key={item.value}
              onClick={() => openEnumCategory(item)}
              className={`flex items-center gap-3 rounded-xl bg-white p-5 shadow-sm cursor-pointer hover:shadow-md transition-shadow ${selectedEnum?.value === item.value ? 'ring-2 ring-[#E85D04]' : ''}`}
            >
              <span className="rounded-lg p-3" style={{ backgroundColor: `${item.color}20`, color: item.color }}>
                <FolderOpen />
              </span>
              <div className="flex-1">
                <strong>{item.label}</strong>
                <p className="text-sm text-gray-500">{item.count} belge</p>
              </div>
              <button
                onClick={e => { e.stopPropagation(); handleUploadClick(item.value) }}
                title="Bu kategoriye belge yükle"
                className="p-1.5 text-gray-400 hover:text-[#E85D04] hover:bg-orange-50 rounded-lg transition-colors"
              >
                <Upload size={16} />
              </button>
            </article>
          ))}
        </div>
      </div>

      {/* Özel kategoriler */}
      {dynamicItems.length > 0 && (
        <div className="mt-8">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Özel Kategoriler</h2>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {dynamicItems.map(item => (
              <article key={item.id} className="flex items-center gap-3 rounded-xl bg-white p-5 shadow-sm">
                <span className="rounded-lg p-3" style={{ backgroundColor: `${item.color}20`, color: item.color }}>
                  <FolderOpen />
                </span>
                <div className="flex-1">
                  <strong>{item.name}</strong>
                  <p className="text-sm text-gray-500">{item.document_count} belge</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}