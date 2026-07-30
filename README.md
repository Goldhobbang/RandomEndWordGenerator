# Random EndWord Generator

Random Korean word chain (끝말잇기) generator built with pure vanilla JS and a custom dictionary.

## Features
- Random word chain generation following Korean ends-with-word rules
- Animated typing effect with particle burst, screen shake, and glitch effects
- Configurable max word count and max character limit
- Copy to clipboard with instant preview mode
- Responsive dark theme UI

## Tech Stack
- Frontend: HTML, CSS (vanilla), JavaScript
- Dictionary: `words.json` (27,831 Korean nouns)
- Backend script: `endwordgenerator.py` for local chain generation

## Usage
1. Serve the directory with any local HTTP server (required for `fetch('words.json')`)
   ```
   python -m http.server 8000
   ```
2. Open `http://localhost:8000` in a browser
3. Adjust max words and max characters, then click **GENERATE**

## GitHub Pages
Deployed at: https://goldhobbang.github.io/RandomEndWordGenerator/

## Dictionary Format
`words.json` maps single-syllable starting characters to arrays of Korean nouns that begin with that character.