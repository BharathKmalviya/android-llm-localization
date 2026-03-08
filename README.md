# Android Localization AI Scripts

A collection of zero-dependency Python scripts to translate, fix, and verify Android Android `strings.xml` resources using Large Language Models (LLMs) like Google Gemini, OpenAI (ChatGPT), Anthropic (Claude), and Local models (Ollama).

## Why this exists?

Localizing Android apps usually involves paying for services, exporting CSVs, or manually using Google Translate. We wanted a way to automatically translate `strings.xml` directly in the project directory using modern LLMs, which provide significantly better context-aware translations.

These scripts have **ZERO dependencies** (no `pip install` required!) and use Python's built-in networking libraries to keep your developer environment clean.

---

## The Scripts

Find three main tools in this repository:
1. `translate_strings.py`: The main tool. Translates your English strings into all other requested languages.
2. `verify_strings.py`: A safety checker. Validates that translated strings won't crash your app due to malformed format specifiers (e.g. `%1$s`).
3. `fix_strings.py`: A formatter. Fixes common XML and escaping issues caused by LLM hallucinations (like unescaped apostrophes).

---

## 1. Translating Strings (`translate_strings.py`)

This script reads your default `app/src/main/res/values/strings.xml` and translates it into all other `values-*` directories it finds in your project.

### Prerequisites
1. You must have Python 3 installed.
2. Ensure you have the target language folders created (e.g., `values-es/`, `values-hi/`). The script will look for these folders to know which languages to translate to.
3. Get an API Key. **[Google Gemini AI Studio](https://aistudio.google.com/) provides a very generous free tier.**

### Usage

```bash
# Basic usage with Gemini (Default)
python translate_strings.py --api-key YOUR_GEMINI_API_KEY
```

**Customizing the execution:**

```bash
python translate_strings.py \
    --api-key YOUR_API_KEY \
    --provider openai \
    --model gpt-4o-mini \
    --app-context "a fitness tracking and workout logger app" \
    --res-dir app/src/main/res
```

### Full Arguments
| Argument | Description | Default |
|---|---|---|
| `--api-key` | Your API key or set via env vars (`GEMINI_API_KEY`, etc.) | *None* |
| `--provider` | AI Provider to use: `gemini`, `openai`, `anthropic`, `custom` | `gemini` |
| `--model` | specific model to use (e.g. `gemini-2.5-flash`, `gpt-4o`) | defaults to provider standard |
| `--app-context` | Short description of your app to guide the LLM's translation context | *None* |
| `--res-dir` | Path to the Android `res` directory | `app/src/main/res` |
| `--base-url` | Base URL for custom OpenAI-compatible endpoints | *None* |
| `--sleep` | Seconds to sleep between requests to avoid rate limits | `5.0` |

### Using Local Models (Ollama, LM Studio)
If you want to run this entirely locally and for free without API limits, you can connect it to any OpenAI-compatible local server.

```bash
# Example running against a local Ollama server running Llama 3
python translate_strings.py \
    --provider custom \
    --base-url http://localhost:11434/v1/chat/completions \
    --model llama3
```

---

## 2. Verifying Translations (`verify_strings.py`)

LLMs are great, but they can occasionally mess up Android string format specifiers. For example, replacing `%1$s` with `%s` or `%`, which will throw an `UnknownFormatConversionException` and **CRASH** your app.

This script compiles a Java verifier that dry-runs `String.format()` against every translated string using the native Java rules.

### Usage
```bash
python verify_strings.py --res-dir app/src/main/res
```
*Note: Requires `javac` to be in your system PATH. If it fails, run it from the embedded terminal inside Android Studio.*

---

## 3. Fixing Common Issues (`fix_strings.py`)

Sometimes LLMs insert literal unicode apostrophes (`\u2019`) or unescaped single quotes (`'`), which breaks Android's AAPT2 compiler. 

Run this script to automatically clean up and properly escape all strings.xml files.

### Usage
```bash
python fix_strings.py --res-dir app/src/main/res
```

---

## Recommended Workflow

1. Update your English `strings.xml`.
2. Create empty `values-<lang>` folders for the languages you want to support.
3. Run `python translate_strings.py --api-key YOUR_API_KEY`.
4. Run `python fix_strings.py` to fix escaping issues.
5. Run `python verify_strings.py` to ensure no format specifier crashes.
6. Build and test your app!

---
*Created to make Android localization accessible, free, and completely automated.*
