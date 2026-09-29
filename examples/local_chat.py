"""Talk to the harness in the terminal, backed by a local Ollama model.

    ollama pull qwen3:8b
    python examples/local_chat.py                 # type what the caller says
    python examples/local_chat.py --model gemma3:12b --omit-think
    python examples/local_chat.py --language sw        # Swahili canned lines + replies
    python examples/local_chat.py --language lg        # Luganda via machine translation
                                                       # (pip install transformers torch)

Empty line or Ctrl+C = caller hangs up. Prints per-turn latency and the ticket.
"""

from __future__ import annotations

import argparse
import json
import time

from triage import IntakeSession, TranslatingSession
from triage.adapters import OllamaClient
from triage.prompts import LANGUAGE_NAMES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument(
        "--omit-think",
        action="store_true",
        help="don't send think=false (for models without a thinking mode that reject it)",
    )
    parser.add_argument(
        "--language", default="en", help="en or sw talk to the model directly; lg goes through translation"
    )
    parser.add_argument("--translation-model", default="facebook/nllb-200-distilled-600M")
    args = parser.parse_args()

    llm = OllamaClient(args.model, args.host, think=None if args.omit_think else False)
    if args.language in LANGUAGE_NAMES:
        session = IntakeSession(llm, language=args.language)
    else:
        from triage.translation import NLLBTranslator

        print(f"Loading translation model {args.translation_model}...")
        session = TranslatingSession(llm, NLLBTranslator(args.translation_model), args.language)
    print(f"AGENT : {session.opening_line()}")
    try:
        while True:
            text = input("CALLER: ").strip()
            if not text:
                break
            start = time.perf_counter()
            result = session.handle_utterance(text)
            elapsed = time.perf_counter() - start
            print(f"AGENT : {result.reply_text}   [{elapsed:.2f}s]")
            if result.done:
                break
    except (KeyboardInterrupt, EOFError):
        print()
    print("TICKET:", json.dumps(session.finalize().to_dict(), indent=2))


if __name__ == "__main__":
    main()
