// Dashboard labels. English is the reference; Swahili is a draft that needs native-speaker review.
export type UiLang = "en" | "sw";

export const UI_LANGS: Record<UiLang, string> = { en: "English", sw: "Kiswahili" };

export const STRINGS = {
  en: {
    title: "Clinic / CHW Dashboard — sorted by urgency",
    subtitle: "Human closes every ticket. Rules engine decides tier, not LLM.",
    id: "ID", tier: "Tier", caller: "Caller", language: "Language", symptoms: "Symptoms",
    reason: "Reason", status: "Status", close: "Close", empty: "No tickets yet.",
  },
  sw: {
    title: "Dashibodi ya Kliniki / CHW — kwa mpangilio wa uharaka",
    subtitle: "Mhudumu hufunga kila tiketi. Mfumo wa kanuni huamua kiwango, si LLM.",
    id: "Namba", tier: "Kiwango", caller: "Mpigaji", language: "Lugha", symptoms: "Dalili",
    reason: "Sababu", status: "Hali", close: "Funga", empty: "Hakuna tiketi bado.",
  },
} satisfies Record<UiLang, Record<string, string>>;

const TIERS: Record<string, Record<UiLang, string>> = {
  emergency: { en: "Emergency", sw: "Dharura" },
  urgent: { en: "Urgent", sw: "Haraka" },
  self_care: { en: "Self-care", sw: "Kujitunza" },
};

const STATUSES: Record<string, Record<UiLang, string>> = {
  open: { en: "Open", sw: "Wazi" },
  closed: { en: "Closed", sw: "Imefungwa" },
};

// Call languages, including the old "luganda" value stored by earlier builds.
const CALL_LANGS: Record<string, Record<UiLang, string>> = {
  en: { en: "English", sw: "Kiingereza" },
  sw: { en: "Swahili", sw: "Kiswahili" },
  lg: { en: "Luganda", sw: "Kiganda" },
  luganda: { en: "Luganda", sw: "Kiganda" },
  nyn: { en: "Runyankole", sw: "Kinyankole" },
};

// Symptom codes from the triage package, plus the plain names the backend engine uses.
const SYMPTOMS: Record<string, Record<UiLang, string>> = {
  fever: { en: "Fever", sw: "Homa" },
  cough: { en: "Cough", sw: "Kikohozi" },
  difficulty_breathing: { en: "Difficulty breathing", sw: "Shida ya kupumua" },
  fast_breathing: { en: "Fast breathing", sw: "Kupumua haraka" },
  chest_pain: { en: "Chest pain", sw: "Maumivu ya kifua" },
  convulsions: { en: "Convulsions", sw: "Degedege" },
  unconscious: { en: "Unconscious", sw: "Amepoteza fahamu" },
  unable_to_drink: { en: "Unable to drink", sw: "Hawezi kunywa" },
  vomiting_everything: { en: "Vomiting everything", sw: "Anatapika kila kitu" },
  vomiting: { en: "Vomiting", sw: "Kutapika" },
  diarrhoea: { en: "Diarrhoea", sw: "Kuharisha" },
  blood_in_stool: { en: "Blood in stool", sw: "Damu kwenye kinyesi" },
  severe_bleeding: { en: "Severe bleeding", sw: "Kutokwa damu nyingi" },
  bleeding_in_pregnancy: { en: "Bleeding in pregnancy", sw: "Kutokwa damu wakati wa ujauzito" },
  stiff_neck: { en: "Stiff neck", sw: "Shingo ngumu" },
  headache: { en: "Headache", sw: "Maumivu ya kichwa" },
  rash: { en: "Rash", sw: "Vipele" },
  abdominal_pain: { en: "Abdominal pain", sw: "Maumivu ya tumbo" },
  sore_throat: { en: "Sore throat", sw: "Maumivu ya koo" },
  runny_nose: { en: "Runny nose", sw: "Mafua" },
  body_aches: { en: "Body aches", sw: "Maumivu ya mwili" },
  ear_pain: { en: "Ear pain", sw: "Maumivu ya sikio" },
  painful_urination: { en: "Painful urination", sw: "Maumivu wakati wa kukojoa" },
  injury: { en: "Injury", sw: "Jeraha" },
  diarrhea: { en: "Diarrhoea", sw: "Kuharisha" },
  seizure: { en: "Seizure", sw: "Degedege" },
  labour: { en: "Labour", sw: "Uchungu wa kujifungua" },
  stroke: { en: "Stroke", sw: "Kiharusi" },
  dehydration: { en: "Dehydration", sw: "Upungufu wa maji mwilini" },
};

const lookup = (table: Record<string, Record<UiLang, string>>, value: string, lang: UiLang) => {
  const key = value.trim().toLowerCase();
  return table[key]?.[lang] ?? table[key.replace(/ /g, "_")]?.[lang] ?? value.replace(/_/g, " ");
};

export const tierLabel = (v: string, l: UiLang) => lookup(TIERS, v, l);
export const statusLabel = (v: string, l: UiLang) => lookup(STATUSES, v, l);
export const callLangLabel = (v: string, l: UiLang) => lookup(CALL_LANGS, v || "en", l);
export const symptomsLabel = (csv: string, l: UiLang) =>
  csv.split(",").filter((s) => s.trim()).map((s) => lookup(SYMPTOMS, s, l)).join(", ");
