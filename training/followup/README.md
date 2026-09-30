# Follow-up question model

Picks the **next question to ask a caller**. It never writes the question and never decides urgency:

```
answers so far ─► trained symptom model ─► P(yes) for each unasked symptom ─┐
                  rules engine (decide) ─► would a "yes" raise the tier? ───┴─► next question from a fixed bank
```

1. The IMCI danger signs are always asked first, in a fixed order.
2. Then up to 2 follow-ups, scored as `P(yes) × (1 + 100 × tiers a yes would raise)`: the expected change to the outcome. A question that could raise the tier is never dropped for being unlikely.
3. Every question is a fixed line in `triage/followup/bank.py`, with English text and a Swahili draft. So questions can be recorded, translated and cached like the keypad menu. There's no free text to machine-translate or check during a call.

## Files

| Path | What |
|---|---|
| `download_datasets.py` | Downloads the datasets into `data/raw/` (resumes if interrupted) and writes checksums to `data/raw/datasets.lock.json` |
| `symptom_map.py` | Maps dataset symptom names to our 24 codes. **Needs clinician review.** |
| `train.py` | Trains, evaluates and writes `triage/followup/model.json` |
| `data/` | Raw and processed data. Gitignored: the main file is 190 MB, over GitHub's limit |
| `triage/followup/` | Runtime code: `bank.py` (questions), `model.py` (loads the JSON), `policy.py` (picks the next question), `interview.py` (runs a call's questions) |

## Datasets

| Dataset | Kaggle | Direct CSV (used by the script) | Used for |
|---|---|---|---|
| Diseases and Symptoms (dhivyeshrk): 246,945 rows, 377 symptoms | [kaggle](https://www.kaggle.com/datasets/dhivyeshrk/diseases-and-symptoms-dataset) | [hf mirror](https://huggingface.co/datasets/dhivyeshrk/Disease-Symptom-Extensive-Clean/resolve/main/Final_Augmented_dataset_Diseases_and_Symptoms.csv) | Training |
| Disease Symptom Prediction (itachi9604): 4,920 rows, 41 conditions incl. malaria, typhoid, TB | [kaggle](https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset) | [hf mirror](https://huggingface.co/datasets/shanover/disease_symptoms_prec_full/resolve/main/disease_sympts_prec_full.csv) | Training |
| Emergency Service Triage (KTAS) | [kaggle](https://www.kaggle.com/datasets/ilkeryildiz/emergency-service-triage-application) | not included | Evaluation (optional, `--kaggle`) |
| Symptom2Disease | [kaggle](https://www.kaggle.com/datasets/niyarrbarman/symptom2disease) | not included | Evaluation (optional, `--kaggle`) |

If the script can't download a file, download it in a browser and save it as `data/raw/dhivyeshrk_diseases_symptoms.csv` or `data/raw/itachi_disease_symptoms.csv`. Then run the script again: it records the checksums. Check each dataset's license on Kaggle before sharing the data or the model.

## Train

```bash
pip install -r training/followup/requirements.txt    # numpy, scikit-learn (training only)
python training/followup/download_datasets.py
python training/followup/train.py                    # ~3 min on a laptop CPU, no GPU
```

`train.py` trains two candidate models:
- **logistic:** one small logistic regression per symptom. Its weights are readable.
- **mlp:** one small neural network that scores all symptoms at once.

It then simulates 3,000 calls on held-out data and exports the logistic model, unless the network is more than 1 point better. The runtime needs no ML libraries for either model. Options: `--model logistic|mlp`, `--hidden 32`, `--cases 3000`.

## Results (simulated calls, 2 follow-ups after the danger signs, as on the phone line)

| Question order | Matches full-information tier | Under-triaged |
|---|---|---|
| Danger signs only | 86.4% | 13.6% |
| Random | 88.5% | 11.5% |
| Most common first | 91.3% | 8.7% |
| Rules + base rates (no training) | 99.0% | 1.0% |
| **Trained policy** (logistic / mlp) | **99.0% / 99.0%** | **1.0% / 1.0%** |

With 3 follow-ups the trained policy reaches 99.5%, but the extra question costs about 7 seconds per call.

Read these honestly:
- **The design does all of the work here.** Asking what could change the rules engine's decision is what helps. On this data, training adds nothing measurable over base rates (99.0% both).
- **The learned likelihoods are weak.** AUC is mostly 0.5–0.7, because the datasets collapse to only 1,611 distinct combinations of our 24 codes.
- **The evaluation uses the same kind of data as training:** synthetic, and not from Uganda.

Real value will come from retraining on local data. The best source is this system's own tickets once clinicians have closed them. `train.py` takes any source that `load_all()` can turn into symptom sets.

## Use it in this codebase

```python
from triage.followup import FollowUpPolicy

policy = FollowUpPolicy()                  # loads triage/followup/model.json
asked: set[str] = set()                    # question ids already put to the caller

q = policy.next_question(report, asked)    # report: triage.schema.SymptomReport
while q is not None:
    say(q.text(lang))                      # a fixed line: recorded clip, cached Sunbird clip or <Say>
    asked.add(q.id)
    if caller_pressed(q.options) is True:  # "1" -> yes, "2" -> no
        report.add_symptoms([q.symptom])
    q = policy.next_question(report, asked)
decision = decide(report)                  # the rules engine still decides the tier
```

`policy.rank(report, asked)` returns every candidate with its `p_yes` and `tiers_raised`, which is useful for logging why a question was asked.

**Where it's wired in:** `triage/followup/interview.py` (`Interview`) runs the structured part of every phone call in `med-intake/backend/app/voice.py`, on both paths:
danger signs → screening (keypad callers, or speech that matched no symptom) → how long / pregnant / how bad → emergency checks (a yes that would make it an emergency, e.g. fever → stiff neck) → up to 2 follow-ups from this policy → rules engine.
The follow-up questions (`fu_*`) are in the recording scripts and the Sunbird warm-up like every other prompt. For call lengths, see `med-intake/scripts/estimate_call_time.py`.
