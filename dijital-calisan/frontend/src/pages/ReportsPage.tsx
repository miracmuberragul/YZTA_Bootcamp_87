import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { managementApi } from '../api/managementApi'

export default function ReportsPage(){
 const [data,setData]=useState<any>(null); const [error,setError]=useState('')
 useEffect(()=>{managementApi.analytics().then(r=>setData(r.data)).catch(()=>setError('Rapor verileri alınamadı.'))},[])
 if(!data)return <div className="p-8">{error||'Yükleniyor…'}</div>
 const cards=[['Toplam belge',data.total_documents],['Hazır belge',data.processed_documents],['Toplam soru',data.total_questions],['Aktif kullanıcı',data.active_users]]
 return <section className="h-full overflow-auto p-8"><h1 className="text-2xl font-bold">Raporlar</h1>
  <div className="my-6 grid gap-4 md:grid-cols-4">{cards.map(([label,value])=><article key={label} className="rounded-xl bg-white p-5 shadow-sm"><p className="text-sm text-gray-500">{label}</p><strong className="mt-2 block text-3xl">{value}</strong></article>)}</div>
  <article className="rounded-xl bg-white p-6 shadow-sm"><h2 className="mb-5 font-semibold">Son 7 günlük soru sayısı</h2><div className="h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.daily_questions}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date"/><YAxis allowDecimals={false}/><Tooltip/><Bar dataKey="count" fill="#E85D04" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></div></article>
 </section>
}
