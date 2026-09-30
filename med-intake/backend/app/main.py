from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DB_URL
from .triage_engine import triage
from triage.rules.engine import decide
from . import voice as V
engine = create_engine(DB_URL, connect_args={"check_same_thread":False})
Session = sessionmaker(bind=engine)
Base = declarative_base()
class Ticket(Base):
    __tablename__="tickets"
    id=Column(Integer,primary_key=True)
    caller=Column(String,default="")
    lang=Column(String,default="en")
    symptoms=Column(Text,default="")
    tier=Column(String,default="self_care")
    reason=Column(Text,default="")
    confidence=Column(Float,default=0)
    status=Column(String,default="open")
    name=Column(String,default="")
    age=Column(Integer,default=0)
    sex=Column(String,default="")
    village=Column(String,default="")
    diagnosis=Column(Text,default="")
    diagnosed_by=Column(String,default="")
    transcript=Column(Text,default="")
    summary=Column(Text,default="")
Base.metadata.create_all(engine)
for _col, _typ in [("name",String),("age",Integer),("sex",String),("village",String)]:
    try: engine.execute(f"ALTER TABLE tickets ADD COLUMN {_col}") if False else None
    except Exception: pass
try:
    with engine.begin() as _c:
        _have={r[1] for r in _c.exec_driver_sql("PRAGMA table_info(tickets)").all()}
        if "name" not in _have: _c.exec_driver_sql("ALTER TABLE tickets ADD COLUMN name VARCHAR DEFAULT ''")
        if "age" not in _have: _c.exec_driver_sql("ALTER TABLE tickets ADD COLUMN age INTEGER DEFAULT 0")
        if "sex" not in _have: _c.exec_driver_sql("ALTER TABLE tickets ADD COLUMN sex VARCHAR DEFAULT ''")
        if "village" not in _have: _c.exec_driver_sql("ALTER TABLE tickets ADD COLUMN village VARCHAR DEFAULT ''")
        if "diagnosis" not in _have: _c.exec_driver_sql("ALTER TABLE tickets ADD COLUMN diagnosis TEXT DEFAULT ''")
        if "diagnosed_by" not in _have: _c.exec_driver_sql("ALTER TABLE tickets ADD COLUMN diagnosed_by VARCHAR DEFAULT ''")
        if "transcript" not in _have: _c.exec_driver_sql("ALTER TABLE tickets ADD COLUMN transcript TEXT DEFAULT ''")
        if "summary" not in _have: _c.exec_driver_sql("ALTER TABLE tickets ADD COLUMN summary TEXT DEFAULT ''")
except Exception as _e: print("bio migrate skip:",_e)
app = FastAPI(title="Voice Triage Intake")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
class IntakeIn(BaseModel):
    caller: str=""; lang: str="en"; symptoms: list[str]=[]; flags: dict={}
    name: str=""; age: int=0; sex: str=""; village: str=""
    transcript: str=""; summary: str=""
class StatusIn(BaseModel):
    status: str
    diagnosis: str=""
    diagnosed_by: str=""
def _row(r) -> dict:
    return {"id":r.id,"caller":r.caller,"lang":r.lang,"symptoms":r.symptoms,"tier":r.tier,"reason":r.reason,"confidence":r.confidence,"status":r.status,
        "name":getattr(r,"name","") or "","age":getattr(r,"age",0) or 0,"sex":getattr(r,"sex","") or "","village":getattr(r,"village","") or "",
        "diagnosis":getattr(r,"diagnosis","") or "","diagnosed_by":getattr(r,"diagnosed_by","") or "",
        "transcript":getattr(r,"transcript","") or "","summary":getattr(r,"summary","") or ""}
def _band(age:int) -> str:
    try: a=int(age)
    except Exception: return "unknown"
    if a<=0: return "unknown"
    if a<5: return "0-4"
    if a<18: return "5-17"
    if a<60: return "18-59"
    return "60+"
def _summarize(tier: str, symptoms: list[str], bio: dict, transcript: str) -> str:
    """AI summary when LLM configured, else rules-based one-liner. Never decides tier."""
    from .config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TIMEOUT
    who=[]
    if bio.get("name"): who.append(str(bio["name"]))
    if bio.get("sex"): who.append(str(bio["sex"]))
    if bio.get("age"): who.append(f"{bio['age']}y")
    if bio.get("lang"): who.append(str(bio["lang"]))
    who_s=" ".join(who) or "unknown caller"
    sym=", ".join(symptoms) or "no symptoms captured"
    fallback=f"{tier.upper}: {who_s} — {sym_s}." if (sym_s:=sym) else f"{tier.upper}: {who_s}."
    if transcript:
        fallback+=f" Call notes: {transcript[:300]}"
    if LLM_BASE_URL and LLM_MODEL:
        try:
            import requests as _R
            r=_R.post(LLM_BASE_URL.rstrip("/")+"/chat/completions",
                headers={"Authorization":f"Bearer {LLM_API_KEY}"} if LLM_API_KEY else {},
                timeout=LLM_TIMEOUT, json={"model":LLM_MODEL,"temperature":0,"max_tokens":120,
                "messages":[{"role":"system","content":"Summarise this triage call in 2 sentences for a clinician. Symptoms, bio, urgency. No diagnosis."},
                {"role":"user","content":f"tier={tier} symptoms={sym} bio={who_s} transcript={transcript[:1500]}"}]})
            import json as _j
            return _j.loads(r.json()["choices"][0]["message"]["content"]).get("summary") or r.json()["choices"][0]["message"]["content"][:500]
        except Exception as e: print("summary llm fail, rules fallback:",e)
    return fallback
@app.post("/api/intake")
def intake(b: IntakeIn):
    tier,reason,conf=triage(b.symptoms,b.flags)
    summary=b.summary or _summarize(tier,b.symptoms,{"age":b.age,"sex":b.sex,"lang":b.lang,"name":b.name},b.transcript)
    db=Session(); t=Ticket(caller=b.caller,lang=b.lang,symptoms=",".join(b.symptoms),tier=tier,reason=reason,confidence=conf,
        name=b.name,age=b.age,sex=b.sex,village=b.village,transcript=b.transcript,summary=summary)
    db.add(t); db.commit(); db.refresh(t); db.close()
    action={"emergency":"nearest facility + alert","urgent":"CHW callback ticket","self_care":"TTS self-care advice"}[tier]
    return {"id":t.id,"tier":tier,"reason":reason,"confidence":conf,"action":action}
@app.get("/api/tickets")
def lst():
    db=Session()
    rows=db.query(Ticket).order_by(Ticket.id.desc()).all(); db.close()
    order={"emergency":0,"urgent":1,"self_care":2}
    return sorted([_row(r) for r in rows],key=lambda x:order[x["tier"]])
@app.get("/api/stats")
def stats():
    db=Session(); rows=db.query(Ticket).all(); db.close()
    by_tier: dict={}; by_sex: dict={}; by_band: dict={}; by_lang: dict={}; by_village: dict={}
    for r in rows:
        d=_row(r)
        for tbl,key in [(by_tier,d["tier"]),(by_sex,d["sex"] or "unknown"),(by_band,_band(d["age"])),(by_lang,d["lang"]),(by_village,d["village"] or "unknown")]:
            tbl[key]=tbl.get(key,0)+1
    return {"total":len(rows),"open":sum(1 for r in rows if r.status=="open"),
        "by_tier":by_tier,"by_sex":by_sex,"by_age_band":by_band,"by_lang":by_lang,"by_village":by_village}
@app.get("/api/tickets/{tid}")
def one(tid:int):
    db=Session(); t=db.query(Ticket).get(tid); db.close()
    if not t: raise HTTPException(404,"no ticket")
    return _row(t)
@app.post("/api/tickets/{tid}")
def set_status(tid:int,b:StatusIn):
    db=Session(); t=db.query(Ticket).get(tid)
    if not t: raise HTTPException(404,"no ticket")
    t.status=b.status
    if b.diagnosis: t.diagnosis=b.diagnosis
    if b.diagnosed_by: t.diagnosed_by=b.diagnosed_by
    db.commit(); db.close(); return {"ok":True}
@app.post("/voice", response_class=str)
def voice_cb(sessionId: str=Form(""), callerNumber: str=Form(""), dtmfDigits: str=Form(""), recordingUrl: str=Form(""), isActive: str=Form("1")):
    from fastapi.responses import Response
    import requests as R
    if isActive=="0": return Response(content="",media_type="application/xml")
    s=V.get(sessionId)
    if not s:
        s,lines,act=V.start(callerNumber or "",sessionId or None)
        return Response(content=V.render(lines,act),media_type="application/xml")
    text=None
    if recordingUrl:
        try: text=" ".join([]) or None
        except Exception: pass
    tr,lines,act=V.turn(s,text=text,digits=dtmfDigits or None)
    log=s.setdefault("transcript_parts",[])
    if dtmfDigits: log.append(f"caller-key: {dtmfDigits}")
    if text: log.append(f"caller: {text}")
    if lines:
        try: log.append("agent: "+" / ".join(l[2] for l in lines if len(l)>2))
        except Exception: pass
    if act=="triage":
        if "report" in s:  # keypad path: full rules engine over the menu answers
            d=decide(s["report"]); tier=d.tier.value; reason="; ".join(d.reasons); conf=0
            symptoms=[x.value for x in s["report"].symptoms]
            log.append(f"keypad-answers: {s.get('answers',{})}")
        else:
            tier,reason,conf=triage(s["symptoms"],s["flags"]); symptoms=s["symptoms"]
        transcript="\n".join(log)
        summary=_summarize(tier,symptoms,{"age":s.get("age",0),"sex":s.get("sex",""),"lang":s.get("lang",""),"name":s.get("name","")},transcript)
        db=Session(); t=Ticket(caller=s["phone"],lang=s["lang"],symptoms=",".join(symptoms),tier=tier,reason=reason,confidence=conf,
            name=s.get("name",""),age=s.get("age",0),sex=s.get("sex",""),village=s.get("village",""),
            transcript=transcript,summary=summary)
        db.add(t); db.commit(); db.close()
        return Response(content=V.render([V.closing(s["lang"],tier)],"hangup"),media_type="application/xml")
    to="+256700300001" if act=="transfer" else ""
    return Response(content=V.render(lines or [],act,to),media_type="application/xml")
@app.get("/health")
def health(): return {"ok":True}
