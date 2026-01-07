import requests
from django.conf import settings

class DeepLError(Exception):
    pass

def _deepl_base_url() -> str:
    is_free = getattr(settings, "DEEPL_IS_FREE", False)
    return "https://api-free.deepl.com" if is_free else "https://api.deepl.com"

def deepl_translate_many(texts: list[str], source: str, target: str, fmt: str = "text") -> list[str]:
    """
    Appelle DeepL pour traduire plusieurs textes en une requête.
    Retourne la liste traduite dans le même ordre.
    """
    if not settings.DEEPL_AUTH_KEY:
        raise DeepLError("DEEPL_AUTH_KEY is not configured")

    if not texts:
        return []

    url = f"{_deepl_base_url()}/v2/translate"

    # DeepL accepte text=... répété (form-encoded)
    data = [
        ("text", t) for t in texts
    ]
    data += [
        ("source_lang", source.upper()),
        ("target_lang", target.upper()),
    ]

    if fmt == "html":
        data.append(("tag_handling", "html"))
        # Optionnel : plus strict/qualitatif si supporté par ton plan
        # data.append(("tag_handling_version", "v2"))

    headers = {
        "Authorization": f"DeepL-Auth-Key {settings.DEEPL_AUTH_KEY}",
    }

    resp = requests.post(url, data=data, headers=headers, timeout=20)
    if resp.status_code != 200:
        raise DeepLError(f"DeepL error {resp.status_code}: {resp.text[:300]}")

    payload = resp.json()
    translations = payload.get("translations") or []
    # On renvoie dans le même ordre
    return [t.get("text", "") for t in translations]
