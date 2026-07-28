import { FormEvent, useEffect, useState } from 'react'
import { CompanySettings, managementApi } from '../api/managementApi'

export default function SettingsPage() {
  const [settings,setSettings]=useState<CompanySettings|null>(null)
  const [message,setMessage]=useState('')
  useEffect(()=>{managementApi.settings().then(r=>setSettings(r.data)).catch(()=>setMessage('Ayarlar alınamadı.'))},[])
  if(!settings) return <div className="p-8">{message || 'Yükleniyor…'}</div>
  const submit=async(e:FormEvent)=>{e.preventDefault(); try{const r=await managementApi.saveSettings(settings);setSettings(r.data);setMessage('Ayarlar kaydedildi.')}catch{setMessage('Ayarlar kaydedilemedi.')}}
  return <section className="h-full overflow-auto p-8"><h1 className="text-2xl font-bold">Ayarlar</h1>
    <form onSubmit={submit} className="mt-6 max-w-2xl space-y-5 rounded-xl bg-white p-6 shadow-sm">
      <label className="block text-sm font-medium">Şirket adı<input className="mt-1 w-full rounded-lg border px-3 py-2" value={settings.company_name} onChange={e=>setSettings({...settings,company_name:e.target.value})}/></label>
      <div className="grid gap-4 md:grid-cols-3">
        <label className="text-sm">Maks. yükleme (MB)<input type="number" className="mt-1 w-full rounded-lg border px-3 py-2" value={settings.max_upload_mb} onChange={e=>setSettings({...settings,max_upload_mb:+e.target.value})}/></label>
        <label className="text-sm">Kaynak sayısı<input type="number" className="mt-1 w-full rounded-lg border px-3 py-2" value={settings.retrieval_limit} onChange={e=>setSettings({...settings,retrieval_limit:+e.target.value})}/></label>
        <label className="text-sm">Benzerlik eşiği<input type="number" step=".05" className="mt-1 w-full rounded-lg border px-3 py-2" value={settings.min_similarity} onChange={e=>setSettings({...settings,min_similarity:+e.target.value})}/></label>
      </div>
      <label className="block text-sm font-medium">Asistan sistem talimatı<textarea rows={5} className="mt-1 w-full rounded-lg border px-3 py-2" value={settings.system_prompt??''} onChange={e=>setSettings({...settings,system_prompt:e.target.value||null})}/></label>
      <div className="flex items-center gap-4"><button className="rounded-lg bg-[#E85D04] px-5 py-2 text-white">Kaydet</button>{message&&<span className="text-sm text-gray-600">{message}</span>}</div>
    </form>
  </section>
}
