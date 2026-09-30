// Dashboard labels. English is the reference; Swahili is a draft that needs native-speaker review.
export type UiLang = "en" | "sw";

export const UI_LANGS: Record<UiLang, string> = { en: "English", sw: "Kiswahili" };

export const STRINGS = {
  en: {
    title: "Clinic / CHW Dashboard — sorted by urgency",
    subtitle: "Human closes every ticket. Rules engine decides tier, not LLM.",
    id: "ID", tier: "Tier", caller: "Caller", language: "Language", symptoms: "Symptoms",
    reason: "Reason", status: "Status", close: "Close", empty: "No tickets yet.",
    unknownCaller: "unknown", callSummary: "Call summary", noSymptoms: "no symptoms captured",
    viewTranscript: "View full transcript", noTranscript: "No transcript captured for this ticket.",
    doctorDiagnosis: "Doctor diagnosis", diagnosis: "Diagnosis",
    diagnosisPlaceholder: "Clinical findings, prescription, referral…", doctorName: "Doctor name",
    saveDiagnosis: "Save diagnosis", closeWithDiagnosis: "Close with diagnosis", diagnosedBy: "by {name}",
    healthProfile: "Health profile", name: "Name", age: "Age", sex: "Sex", village: "Village",
    confidence: "Confidence", overview: "Overview", openOfTotal: "{open} open / {total} total",
    loading: "Loading…", byTier: "By tier", bySex: "By sex", byAge: "By age group", byLanguage: "By language",
    byVillage: "By village", totalTickets: "Total tickets", openTickets: "Open",
    tierChart: "Tickets by urgency tier", ageChart: "Tickets by age group", sexChart: "Tickets by sex",
    showStats: "Show stats", hideStats: "Hide stats", openCount: "{n} open", filterByTier: "Filter by tier",
    all: "All", noTicketSelected: "No ticket selected", selectTicket: "Select a ticket to see details.",
    triageConsole: "Triage console", navOverview: "Overview", navDashboard: "Dashboard",
    navOperations: "Operations", navQueue: "Triage queue", navSettings: "Settings", navDisplay: "Display",
    opsDashboard: "Operations dashboard", liveNote: "Live from /api/stats, refreshes every 3s.",
    displaySettings: "Display settings", displayNote: "Dashboard language and stats panel visibility.",
    showStatsPanel: "Show stats panel", hideStatsPanel: "Hide stats panel",
    populationStats: "Population stats", ticketDetails: "Ticket details", resizeInspector: "Resize inspector",
    ruleNote: "Rule reasons are shown as written by the rules engine.",
  },
  sw: {
    title: "Dashibodi ya Kliniki / CHW — kwa mpangilio wa uharaka",
    subtitle: "Mhudumu hufunga kila tiketi. Mfumo wa kanuni huamua kiwango, si LLM.",
    id: "Namba", tier: "Kiwango", caller: "Mpigaji", language: "Lugha", symptoms: "Dalili",
    reason: "Sababu", status: "Hali", close: "Funga", empty: "Hakuna tiketi bado.",
    unknownCaller: "hajulikani", callSummary: "Muhtasari wa simu", noSymptoms: "hakuna dalili zilizorekodiwa",
    viewTranscript: "Ona nakala kamili ya mazungumzo", noTranscript: "Hakuna nakala ya mazungumzo kwa tiketi hii.",
    doctorDiagnosis: "Uchunguzi wa daktari", diagnosis: "Uchunguzi",
    diagnosisPlaceholder: "Matokeo ya kliniki, dawa zilizoandikwa, rufaa…", doctorName: "Jina la daktari",
    saveDiagnosis: "Hifadhi uchunguzi", closeWithDiagnosis: "Funga pamoja na uchunguzi", diagnosedBy: "na {name}",
    healthProfile: "Wasifu wa afya", name: "Jina", age: "Umri", sex: "Jinsia", village: "Kijiji",
    confidence: "Uhakika", overview: "Muhtasari", openOfTotal: "{open} wazi / {total} jumla",
    loading: "Inapakia…", byTier: "Kwa kiwango", bySex: "Kwa jinsia", byAge: "Kwa kundi la umri",
    byLanguage: "Kwa lugha", byVillage: "Kwa kijiji", totalTickets: "Tiketi zote", openTickets: "Wazi",
    tierChart: "Tiketi kwa kiwango cha uharaka", ageChart: "Tiketi kwa kundi la umri", sexChart: "Tiketi kwa jinsia",
    showStats: "Onyesha takwimu", hideStats: "Ficha takwimu", openCount: "{n} wazi", filterByTier: "Chuja kwa kiwango",
    all: "Zote", noTicketSelected: "Hakuna tiketi iliyochaguliwa", selectTicket: "Chagua tiketi kuona maelezo.",
    triageConsole: "Kituo cha triage", navOverview: "Muhtasari", navDashboard: "Dashibodi",
    navOperations: "Shughuli", navQueue: "Foleni ya triage", navSettings: "Mipangilio", navDisplay: "Mwonekano",
    opsDashboard: "Dashibodi ya shughuli", liveNote: "Moja kwa moja kutoka /api/stats, husasishwa kila sekunde 3.",
    displaySettings: "Mipangilio ya mwonekano", displayNote: "Lugha ya dashibodi na kuonyesha paneli ya takwimu.",
    showStatsPanel: "Onyesha paneli ya takwimu", hideStatsPanel: "Ficha paneli ya takwimu",
    populationStats: "Takwimu za wagonjwa", ticketDetails: "Maelezo ya tiketi", resizeInspector: "Badilisha ukubwa wa paneli",
    ruleNote: "Sababu za kanuni zinaonyeshwa kama zilivyoandikwa na mfumo wa kanuni (Kiingereza).",
  },
} satisfies Record<UiLang, Record<string, string>>;

const TIERS: Record<string, Record<UiLang, string>> = {
  emergency: { en: "Emergency", sw: "Dharura" },
  urgent: { en: "Urgent", sw: "Haraka" },
  self_care: { en: "Self-care", sw: "Kujitunza" },
};

// Age groups match the rules engine (triage.schema.AgeGroup); old tickets may carry year bands.
const AGE_GROUPS: Record<string, Record<UiLang, string>> = {
  infant: { en: "Baby under 1", sw: "Mtoto mchanga chini ya mwaka 1" },
  child: { en: "Child", sw: "Mtoto" },
  adult: { en: "Adult", sw: "Mtu mzima" },
  elderly: { en: "Over 65", sw: "Mzee zaidi ya miaka 65" },
  unknown: { en: "Unknown", sw: "Haijulikani" },
};

const SEXES: Record<string, Record<UiLang, string>> = {
  m: { en: "Male", sw: "Mwanaume" },
  f: { en: "Female", sw: "Mwanamke" },
  unknown: { en: "Unknown", sw: "Haijulikani" },
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

/** Fill "{name}" placeholders in a UI string. */
export const fmt = (template: string, vars: Record<string, string | number>) =>
  template.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ""));

export const tierLabel = (v: string, l: UiLang) => lookup(TIERS, v, l);
export const ageGroupLabel = (v: string, l: UiLang) => lookup(AGE_GROUPS, v || "unknown", l);
export const sexLabel = (v: string, l: UiLang) => lookup(SEXES, v || "unknown", l);
export const unknownLabel = (v: string, l: UiLang) => (!v || v === "unknown" ? AGE_GROUPS.unknown[l] : v);
export const statusLabel = (v: string, l: UiLang) => lookup(STATUSES, v, l);
export const callLangLabel = (v: string, l: UiLang) => lookup(CALL_LANGS, v || "en", l);
export const symptomsLabel = (csv: string, l: UiLang) =>
  csv.split(",").filter((s) => s.trim()).map((s) => lookup(SYMPTOMS, s, l)).join(", ");
