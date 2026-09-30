# Follow-up question model

Picks the **next question to ask a caller**. It never writes the question and never decides urgency:

```
answers so far ─► trained symptom model ─► P(yes) for each unasked symptom ─┐
                  rules engine (decide) ─► would a "yes" raise the tier? ───┴─► next question from a fixed bank
```

1. The IMCI danger signs are always asked first, in a fixed order.
2. Then up to 3 follow-ups, scored as `P(yes) × (1 + 4 × tiers a yes would raise)`.
3. Every question is a fixed line in `triage/followup/bank.py`, with English text and a Swahili draft. So questions can be recorded, translated and cached like the keypad menu. There's no free text to machine-translate or check during a call.

## Files

| Path | What |
|---|---|
| `download_datasets.py` | Downloads the datasets into `data/raw/` (resumes if interrupted) and writes checksums to `data/raw/datasets.lock.json` |
| `symptom_map.py` | Maps dataset symptom names to our 24 codes. **Needs clinician review.** |
| `train.py` | Trains, evaluates and writes `triage/followup/model.json` |
| `data/` | Raw and processed data. Gitignored: the main file is 190 MB, over GitHub's limit |
| `triage/followup/` | Runtime code: `bank.py` (questions), `model.py` (loads the JSON), `policy.py` (picks the next question) |

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

## Results (simulated calls, 3 follow-ups after the danger signs)

| Question order | Matches full-information tier | Under-triaged |
|---|---|---|
| Danger signs only | 86.4% | 13.6% |
| Random | 88.8% | 11.2% |
| Most common first | 96.2% | 3.8% |
| Rules + base rates (no training) | 98.0% | 2.0% |
| **Trained policy** (logistic / mlp) | **98.3% / 98.4%** | **1.7% / 1.6%** |

Read these honestly:
- **The design does most of the work.** Asking what could change the rules engine's decision is what helps. Training adds about 0.3 points.
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

**Where it plugs in (not wired up yet):**
- **Speech path** (`med-intake/backend/app/voice.py`): after the caller describes their symptoms and extraction runs, ask the policy's questions with `<GetDigits>` before triage. That brings follow-up questions to the phone line with no LLM.
- **Keypad path:** replace `dtmf.next_question(answers)` (fixed order) with the policy, so the menu gets shorter and adapts to the caller.
- **LLM harness** (`triage/harness.py`): use `q.text(language)` as the reply when the model's reply is rejected or missing.
- **Recordings and cache:** the new questions in `triage.followup.NEW_PROMPTS` (`fu_*` ids) need adding to the recording scripts and Sunbird warm-up, like the keypad prompts.
