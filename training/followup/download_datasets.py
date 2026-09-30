"""Download the follow-up question model's datasets into training/followup/data/raw/.

    python training/followup/download_datasets.py            # training data (public mirrors)
    python training/followup/download_datasets.py --kaggle   # + Kaggle-only evaluation sets

Downloads resume if interrupted (the larger file is ~190 MB). After each download
the file's size and SHA-256 are written to data/raw/datasets.lock.json, so a
teammate can check they trained on exactly the same data.

Kaggle-only datasets need the kaggle CLI (pip install kaggle) and an API token in
~/.kaggle/kaggle.json. They are optional: training only needs the first two.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parent / "data" / "raw"

DATASETS = [
    {
        "name": "diseases_and_symptoms",
        "file": "dhivyeshrk_diseases_symptoms.csv",
        "url": "https://huggingface.co/datasets/dhivyeshrk/Disease-Symptom-Extensive-Clean/resolve/main/"
        "Final_Augmented_dataset_Diseases_and_Symptoms.csv",
        "kaggle": "dhivyeshrk/diseases-and-symptoms-dataset",
        "use": "training: which symptoms occur together (377 symptom columns)",
    },
    {
        "name": "disease_symptom_description",
        "file": "itachi_disease_symptoms.csv",
        "url": "https://huggingface.co/datasets/shanover/disease_symptoms_prec_full/resolve/main/"
        "disease_sympts_prec_full.csv",
        "kaggle": "itachi9604/disease-symptom-description-dataset",
        "use": "training: tropical conditions (malaria, typhoid, dengue, TB, ...)",
    },
]

KAGGLE_ONLY = [
    {
        "name": "ktas_triage",
        "kaggle": "ilkeryildiz/emergency-service-triage-application",
        "use": "evaluation: emergency-department acuity (KTAS 1-5) by chief complaint",
    },
    {
        "name": "symptom2disease",
        "kaggle": "niyarrbarman/symptom2disease",
        "use": "evaluation: plain-language symptom descriptions for the extraction step",
    },
]


def remote_size(url: str) -> int | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as response:
            return int(response.headers["Content-Length"])
    except Exception:  # noqa: BLE001 - size check is best effort
        return None


def download(url: str, dest: Path, attempts: int = 12) -> None:
    """Resumable download (HTTP Range). A file is only accepted once it has the
    server's full size: the CDN sometimes ends a transfer early without an error."""
    part = dest.with_suffix(dest.suffix + ".part")
    total = remote_size(url)
    for attempt in range(1, attempts + 1):
        have = part.stat().st_size if part.exists() else 0
        if total and have >= total:
            break
        request = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if have and response.status != 206:  # server ignored the range: start over
                    have = 0
                with part.open("ab" if have else "wb") as out:
                    shutil.copyfileobj(response, out, length=1 << 20)
        except Exception as exc:  # noqa: BLE001 - retry any network error
            print(f"  attempt {attempt}: {exc}")
        got = part.stat().st_size if part.exists() else 0
        if total is None or got >= total:
            break
        print(f"  attempt {attempt}: {got:,} of {total:,} bytes, resuming")
        time.sleep(min(2 * attempt, 10))
    got = part.stat().st_size if part.exists() else 0
    if total and got != total:
        raise SystemExit(f"incomplete download ({got:,} of {total:,} bytes): {url}\n"
                         f"Download it in a browser and save it as {dest}")
    part.replace(dest)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kaggle", action="store_true", help="also fetch the Kaggle-only evaluation sets")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    lock_path = RAW / "datasets.lock.json"
    lock = json.loads(lock_path.read_text()) if lock_path.exists() else {}

    for ds in DATASETS:
        dest = RAW / ds["file"]
        total = remote_size(ds["url"])
        if dest.exists() and total and dest.stat().st_size != total:  # truncated earlier download
            dest.replace(dest.with_suffix(dest.suffix + ".part"))
        if dest.exists():
            print(f"{ds['name']}: already at {dest}")
        else:
            print(f"{ds['name']}: downloading ({ds['use']})")
            download(ds["url"], dest)
        lock[ds["name"]] = {"file": ds["file"], "source": ds["url"], "kaggle": ds["kaggle"],
                            "bytes": dest.stat().st_size, "sha256": sha256(dest)}

    if args.kaggle:
        if not shutil.which("kaggle"):
            raise SystemExit("kaggle CLI not found: pip install kaggle, then add ~/.kaggle/kaggle.json")
        for ds in KAGGLE_ONLY:
            target = RAW / ds["name"]
            print(f"{ds['name']}: kaggle datasets download {ds['kaggle']} ({ds['use']})")
            subprocess.run(["kaggle", "datasets", "download", ds["kaggle"], "-p", str(target), "--unzip"], check=True)
            lock[ds["name"]] = {"dir": ds["name"], "kaggle": ds["kaggle"]}

    lock_path.write_text(json.dumps(lock, indent=2) + "\n")
    print(f"done. checksums in {lock_path}")


if __name__ == "__main__":
    main()
