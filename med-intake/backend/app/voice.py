"""Voice agent. Ported from SavaWatch voice.py: AT Voice XML + DTMF fallback + LLM extract slot.

Every spoken line is a ``(lang, prompt_id, text)`` triple. How it is voiced:
1. RECORDED_LANGS play the native-speaker clip at AUDIO_BASE_URL/<lang>/<prompt_id>.mp3
   (see ``triage.dtmf.recording_script``);
2. SUNBIRD_TTS_LANGS are spoken by a Sunbird voice, machine-translating English
   fallbacks for languages with no written script yet (see ``speech``);
3. anything else is read by the Africa's Talking <Say> voice.
English/Swahili callers speak freely. Luganda/Runyankole callers also speak when
Sunbird is configured (SUNBIRD_SPEECH_LANGS); otherwise they use the keypad menu.
Any caller whose speech can't be understood twice finishes on the keypad menu.
"""
import re, uuid, requests
from concurrent.futures import ThreadPoolExecutor
from xml.sax.saxutils import escape
from .config import (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TIMEOUT, VOICE_NAME, AUDIO_BASE_URL, RECORDED_LANGS,
    SUNBIRD_SPEECH_LANGS, SUNBIRD_TTS_LANGS)
from . import speech
from triage import dtmf, prompts
from triage.followup import FollowUpPolicy, Interview
from triage.followup.interview import QUESTIONS
from triage.keywords import symptoms_in
_sessions: dict = {}
POLICY = FollowUpPolicy()  # loads triage/followup/model.json once
LANG_KEYS = {"1":"en","2":"sw","3":"lg","4":"nyn"}
WRITTEN_LANGS = {"en","sw"}  # languages the symptom extraction and the canned scripts are written in
# Free speech -> STT -> extraction; the other languages use the keypad menu.
SPEECH_LANGS = WRITTEN_LANGS | (SUNBIRD_SPEECH_LANGS if speech.enabled() else set())
DYNAMIC_PROMPTS = {"reply","ref_digits"}  # generated per call, never a recorded clip
SAY_ONLY_PROMPTS = {"ref_digits"}  # unique per call: read by the instant <Say> voice, never sent to TTS
_voicer = ThreadPoolExecutor(max_workers=4)
NURSE_KEY = "0"
MAX_INVALID_KEYS = 3
def extract_codes(text:str)->list:
    """Symptom codes (triage.schema.Symptom) from what the caller said: danger-sign
    and keyword patterns in English/Swahili, plus an LLM's reading when one is set.
    Only a starting point: the interview then asks the danger signs and key facts."""
    codes=symptoms_in(text)
    if LLM_BASE_URL and LLM_MODEL:
        try:
            r=requests.post(LLM_BASE_URL.rstrip("/")+"/chat/completions",
                headers={"Authorization":f"Bearer {LLM_API_KEY}"} if LLM_API_KEY else {},
                timeout=LLM_TIMEOUT, json={"model":LLM_MODEL,"temperature":0,"max_tokens":100,
                "messages":[{"role":"system","content":"The caller may speak English or Swahili. List the symptoms they describe as JSON: {\"symptoms\": [plain English names]}. No diagnosis."},
                {"role":"user","content":text}]})
            import json; names=json.loads(r.json()["choices"][0]["message"]["content"]).get("symptoms",[])
            codes+=[c for c in symptoms_in(", ".join(map(str,names))) if c not in codes]
        except Exception as e: print("llm extract fail, keywords only:",e)
    return codes
def line(lang:str,prompt_id:str,text:str|None=None):
    return (lang,prompt_id,dtmf.system_text(prompt_id,lang) if text is None else text)
def question(lang:str,q):
    return (lang,q.id,q.text(lang))
def closing(lang:str,tier:str):
    return (lang,f"closing_{tier}",prompts.closing_line(tier,lang if lang in WRITTEN_LANGS else "en"))
def reference_lines(lang:str,ref:str)->list:
    """'Your reference number is' (a fixed, cacheable clip) + 'M E D, 4 2' read by <Say>.
    The digits are new on every call, so synthesising them would add ~10 s to hang-up."""
    return [line(lang,"your_reference"),(lang,"ref_digits",f"M E D, {' '.join(ref.replace('MED-',''))}.")]
def translate_for_caller(text:str,lang:str)->str:
    """English text (e.g. an SMS) in the caller's language when Sunbird can translate it.
    Keep safety words (like the urgency tier) out of text sent here: machine
    translation can get them wrong (Urgent came back as a word for 'easy')."""
    return text if lang in WRITTEN_LANGS else (speech.translate(text,"en",lang) or text)
def _play(url:str)->str:
    return f'<Play url="{escape(url,{chr(34):"&quot;"})}"/>'
def _speak(lang:str,prompt_id:str,text:str):
    if prompt_id not in DYNAMIC_PROMPTS and AUDIO_BASE_URL and (lang in RECORDED_LANGS or lang==dtmf.ALL_LANGUAGES):
        return _play(f"{AUDIO_BASE_URL}/{dtmf.audio_path(lang,prompt_id)}")
    if prompt_id not in SAY_ONLY_PROMPTS and speech.enabled() and lang in SUNBIRD_TTS_LANGS:
        url=speech.tts_url(speech.in_caller_language(text,lang),lang)
        if url: return _play(url)
    return f'<Say voice="{VOICE_NAME}">{escape(text)}</Say>'
def render(lines:list,action:str,transfer_to:str=""):
    said="".join(_voicer.map(lambda l:_speak(*l),lines))  # uncached Sunbird clips are made in parallel
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
    s={"sid":sid,"phone":phone,"lang":None,"symptoms":[],"flags":{},"answers":{},"invalid":0,
       "bio_stage":None,"sex":"","age":0,"age_band":"","name":"","village":"",
       "visit":None,"ref_buf":"","parent_id":0,"parent":None}
    _sessions[sid]=s
    return s, [_language_menu()], "menu"
BIO_SEX={"1":"M","2":"F"}
# Spoken answers (English + Swahili, needs native-speaker review). Female is checked first.
SEX_WORDS=[("F",r"\b(female|woman|girl|mwanamke|mke|msichana)\b"),("M",r"\b(male|man|boy|mwanaume|mume|mvulana)\b")]
# Age is asked once, with the keypad menu's own age_group question, and stored as
# the ticket's age_band. The rules engine needs these groups (e.g. baby under 1).
AGE_QUESTION=next(q for q in dtmf.MENU if q.id=="age_group")
def age_group_of(age:int)->str:
    """Map a spoken age in years onto the triage age groups."""
    if age<1: return "infant"
    if age<=12: return "child"
    if age<65: return "adult"
    return "elderly"
def uses_speech(s)->bool:
    """Free speech for this call, unless it fell back to the keypad menu."""
    return s["lang"] in SPEECH_LANGS and s.get("mode")!="keypad"
def interview(s)->Interview:
    """This call's structured questions (triage.followup.Interview), made once the
    caller's sex and age are known."""
    if "iv" not in s: s["iv"]=Interview(POLICY,sex=s.get("sex",""),age_group=s.get("age_band",""))
    return s["iv"]
def ask_next(s,intro:list|None=None):
    """Ask the interview's next question, or go to triage when it has nothing left
    to ask (or the answers already add up to an emergency)."""
    q=interview(s).next_question()
    if q is None:
        s["report"]=s["iv"].finish(); return None,None,"triage"
    s["q"]=q.id
    return None,(intro or [])+[question(s["lang"],q)],"menu"
def first_symptom_step(s,intro:list|None=None):
    """First symptom step after the bio questions (or after a follow-up lookup):
    speech callers describe the problem in their own words; keypad callers go
    straight to the questions."""
    lang=s["lang"]; intro=intro or []
    if uses_speech(s): return None,intro+[line(lang,"describe_symptoms")],"listen"
    return ask_next(s,intro or [line(lang,"welcome")])
def resume_follow_up(s,found:dict):
    """A returning caller's ticket was found: reuse their details and go to symptoms."""
    for k in ("sex","age_band","village","name"): s[k]=found.get(k,"") or s.get(k,"")
    s["parent_id"]=found["id"]; s["parent"]=found; s["visit"]="returning"; s["bio_stage"]=None
    return first_symptom_step(s,[line(s["lang"],"welcome_back")])
def ref_not_found(s):
    s["ref_buf"]=""; s["visit"]="ask"
    return None,[line(s["lang"],"ref_not_found"),line(s["lang"],"visit_type")],"menu"
def _bio_prompt(stage:str,lang:str):
    return line(lang,"bio_sex") if stage=="sex" else question(lang,AGE_QUESTION)
def turn(s,text=None,digits=None):
    key=(digits or "")[:1]
    if not s.get("lang"):
        lang=LANG_KEYS.get(key)
        if not lang: return None,[_language_menu()],"menu"
        s["lang"]=lang; s["visit"]="ask"
        return None,[line(lang,"visit_type")],"menu"
    if digits==NURSE_KEY: return None,[line(s["lang"],"connecting_nurse")],"transfer"  # at any point after language
    # Visit type: 1 = new, 9 = follow-up (enter MED digits + #). Asked right after language.
    if s.get("visit")=="ask":
        if key=="9":
            s["visit"]="ref"
            return None,[line(s["lang"],"ref_prompt")],"menu"
        s["visit"]="new"; s["bio_stage"]="sex"
        return None,[_bio_prompt("sex",s["lang"])],"menu"
    if s.get("visit")=="ref":
        digits=(digits or "")
        if "#" in digits:
            s["ref_buf"]+=digits.split("#")[0]
            return s["ref_buf"],[],"lookup_ref"
        if digits:
            s["ref_buf"]+=digits
            if len(s["ref_buf"])>=6: return s["ref_buf"],[],"lookup_ref"
            return None,[],"menu"  # keep collecting, no replay
        if text:
            s["ref_buf"]+="".join(ch for ch in text if ch.isdigit())
            if s["ref_buf"]: return s["ref_buf"],[],"lookup_ref"
        return None,[line(s["lang"],"ref_prompt")],"menu"
    # Bio stage first: sex -> age -> symptoms. Keypad answers for every language;
    # spoken answers are understood when a transcript is available.
    if s.get("bio_stage")=="sex":
        low=(text or "").lower()
        spoken=next((sex for sex,pattern in SEX_WORDS if re.search(pattern,low)),None)
        if key in BIO_SEX or spoken: s["sex"]=BIO_SEX.get(key) or spoken
        elif not s.get("bio_retry"): s["bio_retry"]=True; return None,[line(s["lang"],"invalid_key"),_bio_prompt("sex",s["lang"])],"menu"
        else: s["sex"]=""
        s["bio_stage"]="age"; s.pop("bio_retry",None); return None,[_bio_prompt("age",s["lang"])],"menu"
    if s.get("bio_stage")=="age":
        m=re.search(r"\b(\d{1,3})\b",text or "")
        if key in AGE_QUESTION.options:
            s["age_band"]=AGE_QUESTION.options[key].value
        elif m: s["age"]=int(m.group(1)); s["age_band"]=age_group_of(s["age"])
        elif not s.get("bio_retry2"): s["bio_retry2"]=True; return None,[line(s["lang"],"invalid_key"),_bio_prompt("age",s["lang"])],"menu"
        s["bio_stage"]=None; s.pop("bio_retry2",None)
        return first_symptom_step(s)
    lang=s["lang"]
    if uses_speech(s):
        if not (text or "").strip():
            if not s.get("stt_retry"):
                s["stt_retry"]=True
                return None,[line(lang,"not_heard"),line(lang,"describe_symptoms")],"listen"
            # Speech failed twice: finish on the keypad questions (never self-care by default).
            s["mode"]="keypad"; s["flags"]={**s["flags"],"no_audio":True}
            return ask_next(s,[line(lang,"use_keypad")])
        s.pop("stt_retry",None)
        if lang not in WRITTEN_LANGS:  # e.g. Luganda: extraction reads English
            english=speech.translate(text,lang,"en") or ""
            if not english.strip():  # can't understand it: finish on the keypad questions
                s["mode"]="keypad"
                return ask_next(s,[line(lang,"use_keypad")])
            s["last_translation"]=english; text=english
        codes=extract_codes(text or "")
        interview(s).add_mentioned(codes); s["symptoms"]=[c.value for c in codes]
        s["mode"]="keypad"  # the description is in; the rest of the call is keypad questions
        _,lines,act=ask_next(s)  # a spoken danger sign goes straight to triage
        return text,lines,act
    # Keypad questions from the interview: danger signs, key facts, follow-ups.
    iv=interview(s); qid=s.get("q")
    if qid is None: return ask_next(s,[line(lang,"welcome")])
    if not iv.answer(qid,key):
        s["invalid"]+=1
        if s["invalid"]>=MAX_INVALID_KEYS:  # unfinished -> incomplete report -> CHW callback, never self-care
            s["report"]=iv.finish(complete=False); return None,None,"triage"
        return None,[line(lang,"invalid_key"),question(lang,QUESTIONS[qid])],"menu"
    s["invalid"]=0
    _,lines,act=ask_next(s)
    return qid,lines,act
def get(sid): return _sessions.get(sid)
