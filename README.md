# Random EndWord Generator

Random Korean word chain (끝말잇기) generator built with pure vanilla JS and a custom dictionary.

## Features
- Random word chain generation following Korean ends-with-word rules
- Animated typing effect with particle burst, screen shake, and glitch effects
- Configurable max word count and max character limit
- Copy to clipboard with instant preview mode
- Custom word management: add / list (sorted) / search / edit / delete via `custom.html`
- Every generated chain contains at least one custom word (when any are defined)
- Responsive dark theme UI

## Tech Stack
- Frontend: HTML, CSS (vanilla), JavaScript
- Dictionary: `words.json` (27,831 Korean nouns)
- Custom words: browser `localStorage` (key `endword.customWords.v1`)
- Backend script: `endwordgenerator.py` for local chain generation

## Usage
1. Serve the directory with any local HTTP server (required for `fetch('words.json')`)
   ```
   python -m http.server 8000
   ```
2. Open `http://localhost:8000` in a browser
3. Adjust max words and max characters, then click **GENERATE**
4. (Optional) Click **커스텀 단어 →** in the top-right to manage custom words

## GitHub Pages
Deployed at: https://goldhobbang.github.io/RandomEndWordGenerator/

## Dictionary Format
`words.json` maps single-syllable starting characters to arrays of Korean nouns that begin with that character.

## Custom Words

Open `custom.html` (or click the link on the main page) to manage custom words.

- **Add** — type a word (>=2 chars, no whitespace) and press **Enter**.
- **List** — sorted automatically by Korean codepoint.
- **Search** — substring filter, live.
- **Edit** — click `편집`, change the value, press **Enter** (or click `저장`); **Esc** cancels.
- **Delete** — click `삭제` and confirm.

### Persistence

Custom words live in browser `localStorage` under the key `endword.customWords.v1`. They survive reloads but are scoped to the browser/device/profile — clearing site data wipes them. They are NOT stored in `words.json` or any committed file.

### Chain guarantee

When at least one custom word is defined, every generated chain on `index.html` contains at least one of them, placed around the middle (roughly 40–60% of the way in) instead of always at the front. Implementation: the generator builds a normal chain and, once it reaches the target mid-point, injects a compatible custom word and keeps going; if mid-injection fails after retries it falls back to slot-splicing, end-appending, front-seeding, or a minimal 2-word chain so inclusion is always guaranteed. The chain still satisfies the standard validation rules (link rule, no duplicates, overlap-merge).