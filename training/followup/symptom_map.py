"""Dataset symptom names -> the app's closed symptom vocabulary (triage.schema.Symptom).

Anything not listed is dropped. Mappings lean cautious: when a dataset symptom
could mean a danger sign, it maps to the danger sign (e.g. fainting ->
unconscious). NEEDS CLINICIAN REVIEW before real use.

No dataset covers INJURY or VOMITING_EVERYTHING, so the model has no data for
them; the policy falls back to their base rate (0) and never ranks them. Danger
signs are asked in a fixed order anyway, so the model's gaps there don't matter.
"""

from triage.schema import Symptom as S

# dhivyeshrk/diseases-and-symptoms-dataset: 377 binary symptom columns.
DHIVYESHRK = {
    "fever": S.FEVER,
    "feeling hot": S.FEVER,
    "feeling hot and cold": S.FEVER,
    "cough": S.COUGH,
    "coughing up sputum": S.COUGH,
    "shortness of breath": S.DIFFICULTY_BREATHING,
    "difficulty breathing": S.DIFFICULTY_BREATHING,
    "wheezing": S.DIFFICULTY_BREATHING,
    "apnea": S.DIFFICULTY_BREATHING,
    "abnormal breathing sounds": S.DIFFICULTY_BREATHING,
    "breathing fast": S.FAST_BREATHING,
    "sharp chest pain": S.CHEST_PAIN,
    "chest tightness": S.CHEST_PAIN,
    "burning chest pain": S.CHEST_PAIN,
    "seizures": S.CONVULSIONS,
    "fainting": S.UNCONSCIOUS,
    "infant feeding problem": S.UNABLE_TO_DRINK,
    "vomiting": S.VOMITING,
    "diarrhea": S.DIARRHOEA,
    "blood in stool": S.BLOOD_IN_STOOL,
    "melena": S.BLOOD_IN_STOOL,
    "rectal bleeding": S.BLOOD_IN_STOOL,
    "vomiting blood": S.SEVERE_BLEEDING,
    "spotting or bleeding during pregnancy": S.BLEEDING_IN_PREGNANCY,
    "neck stiffness or tightness": S.STIFF_NECK,
    "headache": S.HEADACHE,
    "frontal headache": S.HEADACHE,
    "skin rash": S.RASH,
    "sharp abdominal pain": S.ABDOMINAL_PAIN,
    "burning abdominal pain": S.ABDOMINAL_PAIN,
    "lower abdominal pain": S.ABDOMINAL_PAIN,
    "upper abdominal pain": S.ABDOMINAL_PAIN,
    "sore throat": S.SORE_THROAT,
    "throat irritation": S.SORE_THROAT,
    "swollen or red tonsils": S.SORE_THROAT,
    "coryza": S.RUNNY_NOSE,
    "nasal congestion": S.RUNNY_NOSE,
    "ache all over": S.BODY_ACHES,
    "muscle pain": S.BODY_ACHES,
    "joint pain": S.BODY_ACHES,
    "ear pain": S.EAR_PAIN,
    "pulling at ears": S.EAR_PAIN,
    "painful urination": S.PAINFUL_URINATION,
}

# itachi9604/disease-symptom-description-dataset: comma-separated symptom lists.
ITACHI = {
    "high_fever": S.FEVER,
    "mild_fever": S.FEVER,
    "cough": S.COUGH,
    "breathlessness": S.DIFFICULTY_BREATHING,
    "chest_pain": S.CHEST_PAIN,
    "coma": S.UNCONSCIOUS,
    "altered_sensorium": S.UNCONSCIOUS,
    "vomiting": S.VOMITING,
    "diarrhoea": S.DIARRHOEA,
    "bloody_stool": S.BLOOD_IN_STOOL,
    "stomach_bleeding": S.SEVERE_BLEEDING,
    "stiff_neck": S.STIFF_NECK,
    "headache": S.HEADACHE,
    "skin_rash": S.RASH,
    "red_spots_over_body": S.RASH,
    "abdominal_pain": S.ABDOMINAL_PAIN,
    "stomach_pain": S.ABDOMINAL_PAIN,
    "belly_pain": S.ABDOMINAL_PAIN,
    "throat_irritation": S.SORE_THROAT,
    "patches_in_throat": S.SORE_THROAT,
    "runny_nose": S.RUNNY_NOSE,
    "muscle_pain": S.BODY_ACHES,
    "joint_pain": S.BODY_ACHES,
    "burning_micturition": S.PAINFUL_URINATION,
}
