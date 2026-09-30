"""Settings. Ported from SavaWatch config.py -> medical intake."""
import os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
try: import triage  # noqa: F401  (pip install -e <repo root>)
except ImportError: sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
def _load_env():
    f = os.path.join(os.path.dirname(BASE), ".env")
    if os.getenv("MED_INTAKE_SKIP_DOTENV")=="1" or not os.path.exists(f): return  # tests set this
    for line in open(f, encoding="utf-8"):
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k,v=line.split("=",1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
_load_env()
AT_USERNAME=os.getenv("AT_USERNAME","sandbox")
AT_API_KEY=os.getenv("AT_API_KEY","")
DRY_RUN=(not AT_API_KEY) or os.getenv("DRY_RUN","0")=="1"
DB_URL=os.getenv("DB_URL","sqlite:///./tickets.db")
PORT=int(os.getenv("PORT","8000"))
LLM_BASE_URL=os.getenv("LLM_BASE_URL","")
LLM_API_KEY=os.getenv("LLM_API_KEY","")
LLM_MODEL=os.getenv("LLM_MODEL","")
LLM_TIMEOUT=float(os.getenv("LLM_TIMEOUT","4"))
PUBLIC_URL=os.getenv("PUBLIC_URL","").rstrip("/")
VOICE_NAME=os.getenv("VOICE_NAME","woman")
AUDIO_BASE_URL=os.getenv("AUDIO_BASE_URL","").rstrip("/")  # recorded clips, see triage.dtmf.recording_script
RECORDED_LANGS={x.strip() for x in os.getenv("RECORDED_LANGS","lg,nyn").split(",") if x.strip()}
GROQ_API_KEY=os.getenv("GROQ_API_KEY","")
STT_MODEL=os.getenv("STT_MODEL","whisper-large-v3-turbo")
STT_TIMEOUT=float(os.getenv("STT_TIMEOUT","20"))
WISPRFLOW_API_KEY=os.getenv("WISPRFLOW_API_KEY","")
WISPRFLOW_TIMEOUT=float(os.getenv("WISPRFLOW_TIMEOUT","30"))
ELEVENLABS_API_KEY=os.getenv("ELEVENLABS_API_KEY","")
ELEVENLABS_STT_MODEL=os.getenv("ELEVENLABS_STT_MODEL","scribe_v1")
def _set(name:str,default:str)->set[str]:
    return {x.strip() for x in os.getenv(name,default).split(",") if x.strip()}
# Sunbird AI (https://docs.sunbird.ai): speech-to-text, text-to-speech and translation.
SUNBIRD_API_TOKEN=os.getenv("SUNBIRD_API_TOKEN","")
SUNBIRD_BASE_URL=os.getenv("SUNBIRD_BASE_URL","https://api.sunbird.ai")
SUNBIRD_TIMEOUT=float(os.getenv("SUNBIRD_TIMEOUT","30"))
SUNBIRD_LIVE_TTS_TIMEOUT=float(os.getenv("SUNBIRD_LIVE_TTS_TIMEOUT","8"))  # a caller is waiting; else <Say>
SUNBIRD_SPEECH_LANGS=_set("SUNBIRD_SPEECH_LANGS","lg,nyn")   # keypad-only langs that get free speech via Sunbird
SUNBIRD_STT_FIRST=_set("SUNBIRD_STT_FIRST","sw,lg,nyn")     # try Sunbird before the other STT providers
SUNBIRD_TTS_LANGS=_set("SUNBIRD_TTS_LANGS","sw,lg,nyn")     # spoken with Sunbird voices instead of the AT <Say> voice
SUNBIRD_VOICES=dict(x.split("=",1) for x in _set("SUNBIRD_VOICES","") if "=" in x)  # e.g. lug=waxal_lug_0002
TTS_CACHE_DIR=os.getenv("TTS_CACHE_DIR",os.path.join(os.path.dirname(BASE),"tts_cache"))
