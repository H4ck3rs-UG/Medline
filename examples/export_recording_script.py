"""Write the keypad-menu recording script for native speakers, one CSV per language.

    python examples/export_recording_script.py                 # all keypad languages
    python examples/export_recording_script.py --language lg --out scripts/

Each row is one clip: its id, the file name the backend will play
(AUDIO_BASE_URL/<audio_file>), the English source, the text to record, and
whether that text still needs translating. Also writes all/language_menu.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from triage.dtmf import ALL_LANGUAGES, KEYPAD_LANGUAGES, recording_script

FIELDS = ["id", "audio_file", "english", "text", "needs_translation"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=sorted([*KEYPAD_LANGUAGES, ALL_LANGUAGES]), action="append")
    parser.add_argument("--out", default="recording_scripts")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for language in args.language or [ALL_LANGUAGES, *KEYPAD_LANGUAGES]:
        rows = recording_script(language)
        path = out / f"{language}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        todo = sum(row["needs_translation"] for row in rows)
        name = KEYPAD_LANGUAGES.get(language, "multi-language")
        print(f"{path}: {len(rows)} clips, {todo} still need a {name} translation")


if __name__ == "__main__":
    main()
