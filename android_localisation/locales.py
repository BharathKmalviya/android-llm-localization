"""Bundled Play listing locales and their Android resource qualifiers."""

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


def all_android_locales():
    """Map the bundled catalog to Android language/region or BCP 47 qualifiers."""
    qualifiers = []
    for locale in GOOGLE_PLAY_LOCALES:
        parts = locale.split("-")
        if len(parts[0]) == 2 and len(parts) == 1:
            qualifier = parts[0]
        elif len(parts[0]) == 2 and len(parts) == 2 and len(parts[1]) == 2:
            qualifier = parts[0] + "-r" + parts[1]
        else:
            qualifier = "b+" + "+".join(parts)
        qualifiers.append(qualifier)
    return qualifiers
