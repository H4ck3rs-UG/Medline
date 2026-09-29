"""Voice agent. Ported from SavaWatch voice.py: AT Voice XML + DTMF fallback + LLM extract slot.

Every spoken line is a ``(lang, prompt_id, text)`` triple. Languages listed in
RECORDED_LANGS play the native-speaker clip at AUDIO_BASE_URL/<lang>/<prompt_id>.mp3
(see ``triage.dtmf.recording_script``); the rest are read out by the provider's
TTS. English/Swahili callers speak freely; Luganda/Runyankole callers answer the
keypad menu in ``triage.dtmf``.
"""
import re, uuid, requests
from xml.sax.saxutils import escape
from .config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TIMEOUT, VOICE_NAME, AUDIO_BASE_URL, RECORDED_LANGS
from triage import dtmf, prompts
from triage.rules.engine import decide
from triage.schema import UrgencyTier
_sessions: dict = {}
LANG_KEYS = {"1":"en","2":"sw","3":"lg","4":"nyn"}
SPEECH_LANGS = {"en","sw"}  # free speech -> STT -> LLM; the other languages use the keypad menu
NURSE_KEY = "0"
MAX_INVALID_KEYS = 3
INTENTS = [("human",["human","agent","nurse","doctor","person","muuguzi","daktari"]),("symptom",["fever","cough","pain","bleed","breath","vomit","diarrhea"]),("bye",["bye","thank","kwaheri","asante"]),]
# Swahili words the keyword fallback maps onto the English symptom names (needs native-speaker review).
SW_SYMPTOMS = {"homa":"fever","kikohozi":"cough","kukohoa":"cough","anakohoa":"cough","kuharisha":"diarrhea","anaharisha":"diarrhea","kuhara":"diarrhea",
    "maumivu ya kifua":"chest pain","kupumua":"difficulty breathing","damu":"bleed","kutapika":"vomit","anatapika":"vomit","maumivu":"pain"}
SEVERE_WORDS = ["severe","heavy","cannot","unconscious","sana","mbaya","hawezi","amezimia"]
def _keyword(text:str):
    t=" "+re.sub(r"[^a-z ]"," ",text.lower())+" "
    for n,ph in INTENTS:
        if any(p in t for p in ph): return n
    return "other"
def extract_symptoms(text:str)->dict:
    """LLM extract slot (OpenAI-compatible). Fallback: keyword flags (English + Swahili)."""
    if LLM_BASE_URL and LLM_MODEL:
        try:
            r=requests.post(LLM_BASE_URL.rstrip("/")+"/chat/completions",
                headers={"Authorization":f"Bearer {LLM_API_KEY}"} if LLM_API_KEY else {},
                timeout=LLM_TIMEOUT, json={"model":LLM_MODEL,"temperature":0,"max_tokens":100,
                "messages":[{"role":"system","content":"The caller may speak English or Swahili. Extract symptoms as JSON: {symptoms:[], severe:bool, duration_days:int}. Write symptom names in English. No diagnosis."},
                {"role":"user","content":text}]})
            import json; return json.loads(r.json()["choices"][0]["message"]["content"])
        except Exception as e: print("llm extract fail, rules fallback:",e)
    low=text.lower()
    found=[p for _,ph in INTENTS for p in ph if p in low]+[en for sw,en in SW_SYMPTOMS.items() if sw in low]
    return {"symptoms":list(dict.fromkeys(found)),"severe":any(w in low for w in SEVERE_WORDS),"duration_days":0}
def line(lang:str,prompt_id:str,text:str|None=None):
    return (lang,prompt_id,dtmf.system_text(prompt_id,lang) if text is None else text)
def question(lang:str,q):
    return (lang,q.id,q.text(lang))
def closing(lang:str,tier:str):
    return (lang,f"closing_{tier}",prompts.closing_line(tier,prompts.normalise_language(lang) if lang in SPEECH_LANGS else "en"))
def _speak(lang:str,prompt_id:str,text:str):
    if AUDIO_BASE_URL and (lang in RECORDED_LANGS or lang==dtmf.ALL_LANGUAGES):
        url=f"{AUDIO_BASE_URL}/{dtmf.audio_path(lang,prompt_id)}"
        return f'<Play url="{escape(url,{chr(34):"&quot;"})}"/>'
    return f'<Say voice="{VOICE_NAME}">{escape(text)}</Say>'
def render(lines:list,action:str,transfer_to:str=""):
    said="".join(_speak(*l) for l in lines)
    if action=="listen":
        body=f'<Record finishOnKey="#" maxLength="15" timeout="5" playBeep="true">{said}</Record>'
    elif action=="menu":
        body=f'<GetDigits numDigits="1" timeout="10" finishOnKey="#">{said}</GetDigits>'
    elif action=="transfer":
        body=said+f'<Dial phoneNumbers="{escape(transfer_to)}" record="true" sequential="true"/>'
    else: body=said
    return '<?xml version="1.0" encoding="UTF-8"?><Response>'+body+"</Response>"
def _language_menu():
    return line(dtmf.ALL_LANGUAGES,dtmf.LANGUAGE_MENU,dtmf.system_text(dtmf.LANGUAGE_MENU))
def start(phone,sid=None):
    sid=sid or uuid.uuid4().hex[:12]
    s={"sid":sid,"phone":phone,"lang":None,"symptoms":[],"flags":{},"answers":{},"invalid":0}
    _sessions[sid]=s
    return s, [_language_menu()], "menu"
def turn(s,text=None,digits=None):
    key=(digits or "")[:1]
    if not s.get("lang"):
        lang=LANG_KEYS.get(key)
        if not lang: return None,[_language_menu()],"menu"
        s["lang"]=lang
        if lang in SPEECH_LANGS: return None,[line(lang,"describe_symptoms")],"listen"
        return None,[line(lang,"welcome"),question(lang,dtmf.MENU[0])],"menu"
    lang=s["lang"]
    if digits==NURSE_KEY: return None,[line(lang,"connecting_nurse")],"transfer"
    if lang in SPEECH_LANGS:
        d=extract_symptoms(text or ""); s["symptoms"]+=d.get("symptoms",[]); s["flags"]={**s["flags"],**{k:v for k,v in d.items() if k!="symptoms"}}
        return text,None,"triage"
    # Keypad menu: one recorded question per call-back, danger signs first.
    q=dtmf.next_question(s["answers"])
    if key not in q.options:
        s["invalid"]+=1
        if s["invalid"]>=MAX_INVALID_KEYS:  # unfinished menu -> incomplete report -> CHW callback, never self-care
            s["report"]=dtmf.report_from_keypresses(s["answers"]); return None,None,"triage"
        return None,[line(lang,"invalid_key"),question(lang,q)],"menu"
    s["invalid"]=0; s["answers"][q.id]=key
    report=dtmf.report_from_keypresses(s["answers"]); nxt=dtmf.next_question(s["answers"])
    if nxt is None or decide(report).tier==UrgencyTier.EMERGENCY:
        s["report"]=report; return q.id,None,"triage"
    return q.id,[question(lang,nxt)],"menu"
def get(sid): return _sessions.get(sid)
