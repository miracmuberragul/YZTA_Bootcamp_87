import { useState, useRef, useEffect } from 'react'
import { Send, FileText, Bot } from 'lucide-react'
import { chatApi } from '../api/chatApi'

interface Source {
  document_name: string
  page: number
  excerpt_preview: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const question = input.trim()
    if (!question || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      const res = await chatApi.ask(question, conversationId)
      const { answer, sources, conversation_id } = res.data.data
      setConversationId(conversation_id)
      setMessages(prev => [...prev, { role: 'assistant', content: answer, sources }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Bir hata oluştu. Lütfen tekrar deneyin.'
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-orange-100 rounded-xl flex items-center justify-center">
            <Bot size={20} className="text-[#E85D04]" />
          </div>
          <div>
            <p className="font-semibold text-gray-800 text-sm">AI Asistan</p>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
              <p className="text-xs text-green-600">Çevrimiçi</p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-orange-100 rounded-2xl flex items-center justify-center mb-4">
              <Bot size={28} className="text-[#E85D04]" />
            </div>
            <p className="text-gray-700 font-medium mb-1">OfficeIQ'ya Hoş Geldiniz</p>
            <p className="text-gray-400 text-sm max-w-xs">
              Şirket belgeleriniz hakkında soru sorun. Cevaplarla birlikte kaynak belgeyi de göreceksiniz.
            </p>
            <div className="mt-6 grid grid-cols-1 gap-2 w-full max-w-sm">
              {[
                'Yıllık izin hakkım kaç gün?',
                'ABC firmasına nasıl teklif verdik?',
                'Masraf beyanı nasıl yapılır?',
              ].map(q => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="text-left text-sm text-gray-600 bg-white border border-gray-200 rounded-xl px-4 py-2.5 hover:border-[#E85D04] hover:text-[#E85D04] transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xl ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
              {/* Bubble */}
              <div className={`rounded-2xl px-4 py-3 text-sm ${msg.role === 'user'
                ? 'bg-[#E85D04] text-white rounded-br-sm'
                : 'bg-white border border-gray-100 text-gray-800 rounded-bl-sm'
                }`}>
                {msg.content}
              </div>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 space-y-1.5">
                  {msg.sources.map((s, j) => (
                    <div key={j} className="flex items-start gap-2 bg-orange-50 border border-orange-100 rounded-xl px-3 py-2">
                      <FileText size={13} className="text-[#E85D04] flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-xs font-medium text-gray-700">{s.document_name} — Sayfa {s.page}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{s.excerpt_preview}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-100 px-6 py-4">
        <div className="flex gap-3">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Sorunuzu yazın..."
            className="flex-1 border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[#E85D04] focus:border-transparent"
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="w-10 h-10 bg-[#E85D04] hover:bg-[#C44D00] disabled:opacity-50 text-white rounded-xl flex items-center justify-center transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}