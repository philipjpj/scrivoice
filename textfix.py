"""Sostituzioni automatiche locali: "parola sbagliata" -> "parola giusta" sul testo trascritto."""
import re


def apply_replacements(text, replacements):
    """replacements: lista di coppie [sbagliata, corretta]. Confronto senza maiuscole/minuscole,
    solo su parole intere; se l'originale inizia con la maiuscola la mantiene."""
    for wrong, right in replacements:
        wrong, right = (wrong or "").strip(), (right or "").strip()
        if not wrong:
            continue
        pattern = re.compile(r"(?<!\w)" + re.escape(wrong) + r"(?!\w)", re.IGNORECASE)

        def repl(m, right=right):
            if m.group(0)[:1].isupper() and right[:1].islower():
                return right[:1].upper() + right[1:]
            return right
        text = pattern.sub(repl, text)
    return text
