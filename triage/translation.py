"""Machine-translation bridge for languages the LLM cannot hold a conversation in.

    caller speech (e.g. Luganda, via SunflowerASR)
        -> translate to English -> IntakeSession (English) -> translate reply back
        -> local-language TTS

The harness itself always runs in English here, so the model, the output guard
and the rules engine behave exactly as they do on the English path. On top of
that:

- The input guard runs on both the original words and the translation, so a
  danger sign lost in translation still closes the call as an emergency.
- Canned lines use a reviewed translation from ``triage.prompts.CANNED`` when
  one exists, instead of a machine translation.
- A translated model reply is checked again by the output guard (it knows
  English and Swahili); if it fails, the canned safe line is spoken instead.
- If translation fails, the model is not called: the caller hears the canned
  line, and repeated failures end the call with a CHW callback (fail safe).

This is an experimental path. Keep the keypad menu (``triage.dtmf``) as the
default for these languages until the translations have been evaluated with
native speakers.
"""

from __future__ import annotations

import logging
from typing import Protocol

from triage import prompts
from triage.guardrails import check_input, reply_violations
from triage.harness import IntakeSession
from triage.llm import LLMClient
from triage.schema import CloseReason, IntakeOutcome, TurnResult

log = logging.getLogger(__name__)


class Translator(Protocol):
    def translate(self, text: str, source: str, target: str) -> str:
        """Translate ``text`` between language codes such as "lg" and "en"."""
        ...


class FakeTranslator:
    """Dictionary lookup, for tests and offline demos. Unknown text passes through."""

    def __init__(self, table: dict[tuple[str, str, str], str] | None = None, fail: bool = False):
        self.table = dict(table or {})
        self.fail = fail
        self.calls: list[tuple[str, str, str]] = []

    def translate(self, text: str, source: str, target: str) -> str:
        self.calls.append((text, source, target))
        if self.fail:
            raise RuntimeError("translation unavailable")
        return self.table.get((text, source, target), text)


# NLLB-200 language codes. NLLB has no Runyankole; plug in a model that does
# (for example one of Sunbird AI's Ugandan-language models) through ``codes``.
NLLB_CODES = {"en": "eng_Latn", "sw": "swh_Latn", "lg": "lug_Latn"}


class NLLBTranslator:
    """Local translation with a Hugging Face NLLB-style model (needs ``transformers`` + ``torch``).

    ``model`` and ``codes`` are configurable so a fine-tuned checkpoint with
    better Ugandan-language coverage can be swapped in.
    """

    def __init__(
        self,
        model: str = "facebook/nllb-200-distilled-600M",
        *,
        codes: dict[str, str] | None = None,
        device: int = -1,
        max_length: int = 400,
    ):
        from transformers import pipeline

        self.codes = dict(NLLB_CODES if codes is None else codes)
        self.max_length = max_length
        self._pipe = pipeline("translation", model=model, device=device)

    def translate(self, text: str, source: str, target: str) -> str:
        if source == target or not text.strip():
            return text
        try:
            src, tgt = self.codes[source], self.codes[target]
        except KeyError as exc:
            raise ValueError(f"no model language code for {exc.args[0]!r}") from None
        result = self._pipe(text, src_lang=src, tgt_lang=tgt, max_length=self.max_length)
        return result[0]["translation_text"].strip()


class TranslatingSession:
    """An English ``IntakeSession`` that speaks to the caller in ``language``."""

    def __init__(self, llm: LLMClient, translator: Translator, language: str, **session_kwargs):
        self.language = language
        self.translator = translator
        self.session = IntakeSession(llm, language="en", **session_kwargs)
        self._translation_failures = 0

    @property
    def done(self) -> bool:
        return self.session.done

    def opening_line(self) -> str:
        return self._to_caller(self.session.opening_line())

    def handle_utterance(self, text: str) -> TurnResult:
        try:
            english = self.translator.translate(text, self.language, "en")
        except Exception:
            log.exception("translation to English failed")
            english = ""
        if english.strip():
            self._translation_failures = 0
            result = self.session.handle_utterance(english, original_text=text)
        elif check_input(text).red_flags:
            # Nothing for the model to read, but the caller's own words carry a
            # danger sign: the harness closes on it before calling the model.
            result = self.session.handle_utterance(text)
        else:
            self._translation_failures += 1
            if self._translation_failures < self.session.max_model_failures:
                return TurnResult(reply_text=self._to_caller(prompts.line("safe_reply")), done=False)
            result = self.session.close(CloseReason.MODEL_FAILURE)
        if result.outcome is not None:
            result.outcome.language = self.language
        return result.model_copy(update={"reply_text": self._to_caller(result.reply_text)})

    def finalize(self) -> IntakeOutcome:
        outcome = self.session.finalize()
        outcome.language = self.language
        return outcome

    def _to_caller(self, english: str) -> str:
        key = prompts.canned_key(english)
        if key is not None and key in prompts.CANNED.get(self.language, {}):
            return prompts.CANNED[self.language][key]
        try:
            translated = self.translator.translate(english, "en", self.language)
        except Exception:
            log.exception("translation to %s failed", self.language)
            return english
        if key is None and reply_violations(translated):
            # The translation introduced something the guard forbids.
            log.warning("translated reply rejected; using canned line")
            return self._to_caller(prompts.CANNED["en"]["safe_reply"])
        return translated
