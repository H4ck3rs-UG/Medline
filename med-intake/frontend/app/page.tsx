"use client";import {useEffect,useState} from "react";
import {STRINGS,UI_LANGS,UiLang,callLangLabel,statusLabel,symptomsLabel,tierLabel} from "./i18n";
const API=process.env.NEXT_PUBLIC_API||"http://localhost:8000";
const LANG_KEY="dashboard-lang";
export default function Page(){
 const [t,setT]=useState<any[]>([]);
 const [lang,setLang]=useState<UiLang>("en");
 useEffect(()=>{try{const v=localStorage.getItem(LANG_KEY);if(v==="en"||v==="sw")setLang(v)}catch{}},[]);
 const pick=(l:UiLang)=>{setLang(l);try{localStorage.setItem(LANG_KEY,l)}catch{}};
 const load=()=>fetch(`${API}/api/tickets`).then(r=>r.json()).then(setT);
 useEffect(()=>{load();const i=setInterval(load,3000);return()=>clearInterval(i)},[]);
 const close=(id:number)=>fetch(`${API}/api/tickets/${id}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({status:"closed"})}).then(load);
 const s=STRINGS[lang];
 return(<main lang={lang} style={{fontFamily:"system-ui",padding:24,maxWidth:1000,margin:"0 auto"}}>
  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:12,flexWrap:"wrap"}}>
   <h1>{s.title}</h1>
   <select aria-label={s.language} value={lang} onChange={e=>pick(e.target.value as UiLang)}>
    {(Object.keys(UI_LANGS) as UiLang[]).map(l=><option key={l} value={l}>{UI_LANGS[l]}</option>)}
   </select>
  </div>
  <p>{s.subtitle}</p>
  <table border={1} cellPadding={8} style={{width:"100%",borderCollapse:"collapse"}}>
   <thead><tr><th>{s.id}</th><th>{s.tier}</th><th>{s.caller}</th><th>{s.language}</th><th>{s.symptoms}</th><th>{s.reason}</th><th>{s.status}</th><th></th></tr></thead>
   <tbody>{t.length===0&&<tr><td colSpan={8}>{s.empty}</td></tr>}
    {t.map(x=><tr key={x.id} style={{background:x.tier==="emergency"?"#fdd":x.tier==="urgent"?"#ffd":"#dfd"}}>
    <td>{x.id}</td><td><b>{tierLabel(x.tier,lang)}</b></td><td>{x.caller}</td><td>{callLangLabel(x.lang,lang)}</td><td>{symptomsLabel(x.symptoms,lang)}</td><td>{x.reason}{x.confidence>0&&` (${x.confidence}%)`}</td><td>{statusLabel(x.status,lang)}</td>
    <td>{x.status==="open"&&<button onClick={()=>close(x.id)}>{s.close}</button>}</td></tr>)}</tbody>
  </table></main>);
}
