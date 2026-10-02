"""Bundled Play listing locales and their Android resource qualifiers."""

import re

# Store-listing locales (not Play Console UI or machine-translation languages).
# Verified on 2026-10-02 against the "View list of available languages" section:
# https://support.google.com/googleplay/android-developer/answer/9844778?hl=en
GOOGLE_PLAY_LOCALES = tuple("""
af sq am ar hy-AM az-AZ bn-BD eu-ES be bg my-MM ca zh-HK zh-CN zh-TW
hr cs-CZ da-DK nl-NL en-AU en-CA en-US en-GB en-IN en-SG en-ZA et fil
fi-FI fr-CA fr-FR gl-ES ka-GE de-DE el-GR gu iw-IL hi-IN hu-HU is-IS id
it-IT ja-JP kn-IN kk km-KH ko-KR ky-KG lo-LA lv lt mk-MK ms-MY ms ml-IN
mr-IN mn-MN ne-NP no-NO fa fa-AE fa-AF fa-IR pl-PL pt-BR pt-PT pa ro rm
ru-RU sr si-LK sk sl es-419 es-ES es-US sw sv-SE ta-IN te-IN th tr-TR uk ur vi
""".split())

_PLAY_TAG = re.compile(r"([A-Za-z]{2,3})(?:-([A-Za-z]{4}))?(?:-([A-Za-z]{2}|[0-9]{3}))?\Z")


def normalize_play_locale(value):
    match = _PLAY_TAG.fullmatch(value.strip())
    if not match or value.strip().lower() == "all":
        raise ValueError("invalid language tag: {!r}; use hi-IN, es-ES or zh-Hant-TW".format(value))
    language, script, region = match.groups()
    return "-".join(part for part in (
        language.lower(), script.title() if script else None, region.upper() if region else None,
    ) if part)


def android_locale(locale):
    """Convert a normalized language tag to an Android resource qualifier."""
    parts = normalize_play_locale(locale).split("-")
    if len(parts[0]) == 2 and len(parts) == 1:
        return parts[0]
    if len(parts[0]) == 2 and len(parts) == 2 and len(parts[1]) == 2:
        return parts[0] + "-r" + parts[1]
    return "b+" + "+".join(parts)


def language_items(value=None, path=None):
    """Combine CLI comma lists with a UTF-8 file of comma/newline lists."""
    items = value.split(",") if value is not None else []
    if path:
        with open(path, "r", encoding="utf-8-sig") as handle:
            for line in handle:
                line = line.split("#", 1)[0].strip()
                if line:
                    items.extend(part.strip() for part in line.split(","))
    return items


def select_locales(items, normalize, bundled, excluded=None, identity=None):
    """Expand all wherever it occurs, preserve order, deduplicate, then exclude."""
    selected = []
    identity = identity or (lambda locale: locale)
    seen = set()
    for item in items:
        additions = bundled if item.strip().lower() == "all" else [normalize(item)]
        for locale in additions:
            if identity(locale) not in seen:
                selected.append(locale)
                seen.add(identity(locale))
    removed = set()
    for item in excluded or []:
        removed.update(identity(locale) for locale in (
            bundled if item.strip().lower() == "all" else [normalize(item)]))
    return [locale for locale in selected if identity(locale) not in removed]


def all_android_locales():
    """Map the bundled catalog to Android language/region or BCP 47 qualifiers."""
    return [android_locale(locale) for locale in GOOGLE_PLAY_LOCALES]
