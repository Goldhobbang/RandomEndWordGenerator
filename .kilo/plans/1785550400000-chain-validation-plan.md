# Korean Word Chain (끝말잇기) Validation Plan

## Goal
1. Create a standalone Python script `validate_chain.py` that checks whether a given string is a valid 끝말잇기 chain string.
2. In the web app (`index.html`), run a validation once whenever a generated string finishes displaying, and show the result in the UI.

## Scope
- Files touched: `validate_chain.py` (new), `index.html` (edit)
- No change to generation algorithm behavior (only returns the chain alongside the text)
- No change to `words.json`, `endwordgenerator.py`, `validate.py`

## Context (current code)
- `index.html` is a single-page app (644 lines, CRLF line endings, Unicode `──` in JS comments).
- `generateChain` at index.html:419-438 builds `chain` but returns only `result` (merged text with overlaps removed).
- Call sites of `generateChain`: index.html:599 and index.html:616, both as `const text = generateChain(maxWords, maxChars);`.
- Animated path completes via `typeAnimate(..., () => { copyBtn.disabled = false; })` (index.html:607-609 and 624+).
- Instant path: `showResultImmediate(result, text, fontSize); copyBtn.disabled = false;` (index.html:611-612 and 630+).
- `#info` element at index.html:290 currently shows the load message only; add a new status element beside it.
- `validate_chain.py` currently contains only a shebang line (placeholder).
- `endwordgenerator.py` already returns `(result, chain)` from its `generate_chain` — mirrors desired JS change.

## Task 1 — Create `validate_chain.py`

Standalone CLI + importable API. Definition of "valid": the string can be split into **2 or more** dictionary words `w1..wn` such that:
- `''.join(w1..wn) == input_string` (words are matched as-is; merged overlaps are naturally handled)
- `wn[i][0] == w_{i-1}[-1]` for all `i >= 1` (chaining rule)
- no duplicate words

### API
```python
def load_dict(path="words.json") -> dict            # start_char -> [words]
def validate_string(s: str, start_dict: dict) -> (bool, list[str], list[str])
    # returns (is_valid, segmentation, errors)
```

### Algorithm (backtracking DFS, longest-match-first)
- Build `word_set` and `by_prefix` index (dict: first char -> words sorted by length desc) from dictionary.
- Recursive `search(pos, prev_word, used, words_so_far)`:
  - If `pos == len(s)`: valid iff `len(words_so_far) >= 2` (and all checks passed on the way).
  - At `pos == 0`: candidates = all words that are a prefix of `s`.
  - At `pos > 0`: candidates = words starting with `prev_word[-1]` that are a prefix of `s[pos:]`.
  - Skip words already in `used`.
  - Try longest candidate first (matches generator's `overlapAppend` behavior and finds a split fast).
- Guards (prevent pathological blowup on noLimit-sized inputs):
  - If `len(s) > 1000`, refuse with error "문자열이 너무 길어 검증 불가".
  - Node budget ~200k recursion nodes; if exceeded, report "검증 시도 횟수 초과".
- Return first successful segmentation, or the collected errors (best-effort reason: "문자열을 사전 단어들로 분할할 수 없음" if no split found).

### CLI
```
python validate_chain.py "<string>" [words.json path]
```
- VALID: print `VALID: <word1> / <word2> / ...`
- INVALID: print `INVALID:` followed by each error line, exit code 1
- VALID: exit code 0

### Known limitation (document in script docstring)
Because the generator merges overlaps, segmentation of the merged string can be ambiguous. A valid generated chain may occasionally be un-segmentable by the standalone script (false INVALID). This is inherent to the input format; the browser-side check (Task 2) uses the actual word chain and is exact.

## Task 2 — Integrate validation into `index.html`

### 2a. `generateChain` returns the chain
Change index.html:437 `return result;` to `return { text: result, chain };`
Update both call sites (index.html:599, 616):
```js
const { text, chain } = generateChain(maxWords, maxChars);
```

### 2b. Add validation + display functions (near word-chain logic, after `generateChain`)
```js
function validateChain(chain) {
    const errors = [];
    if (chain.length < 2) errors.push('단어가 2개 이상 필요합니다');
    for (let i = 1; i < chain.length; i++) {
        const prev = chain[i - 1], curr = chain[i];
        if (curr[0] !== prev[prev.length - 1]) {
            errors.push(`'${prev}'(${prev[prev.length - 1]}) → '${curr}'(${curr[0]}) 연결 오류`);
        }
    }
    const seen = new Set();
    for (const w of chain) {
        if (seen.has(w)) errors.push(`'${w}' 중복 사용`);
        seen.add(w);
    }
    return errors;
}

function showChainStatus(chain) {
    const el = document.getElementById('chainStatus');
    const errors = validateChain(chain);
    if (errors.length === 0) {
        el.textContent = `끝말잇기 검사: 유효 (${chain.length}단어)`;
        el.classList.add('valid');
        el.classList.remove('invalid');
    } else {
        el.textContent = `끝말잇기 검사: 오류 ${errors.length}건 — ${errors.slice(0, 3).join(' / ')}`;
        el.classList.add('invalid');
        el.classList.remove('valid');
    }
}
```

### 2c. Add status element in HTML
After index.html:290 (`<div class="info" id="info"></div>`):
```html
<div class="info" id="chainStatus"></div>
```

### 2d. Add CSS for valid/invalid states (near `.info` rule, index.html ~255)
```css
#chainStatus.valid { color: #6c8; }
#chainStatus.invalid { color: #e88; }
```

### 2e. Call `showChainStatus(chain)` on completion in all 4 paths
- Animated path onComplete (index.html:607-609 and 624+): add `showChainStatus(chain);` inside the `typeAnimate` callback.
- Instant path (index.html:611-612 and 630+): add `showChainStatus(chain);` after `showResultImmediate(...)`.

## Execution Notes (CRITICAL — learned from prior attempts)
- The file uses **CRLF** line endings and Unicode `──` in comments. The `edit` tool and PowerShell `<` heredocs both fail on these lines.
- **Reliable method**: write a Node.js script to a temp file (e.g. `C:\Users\diamo\AppData\Local\Temp\kilo\apply_validation.js`) that does targeted `content.replace()` calls, then run `node <script>`. Match on ASCII-only substrings (e.g. `return result;` with surrounding context, `typeAnimate(result, text, fontSize, () => {`, `showResultImmediate(result, text, fontSize);`) to avoid Unicode matching issues.
- For `validate_chain.py`: create via the Node.js script too (array-of-lines joined with `\n`), or via a `.py` file written with the Write tool in an implementation-capable agent.

## Validation Steps
1. Python:
   - `python validate_chain.py "가나다라"` → expect VALID if dictionary allows a split (e.g. `가나`/`나다`... adjust to actual dictionary words; use a known chain from `endwordgenerator.py` output).
   - Test an obviously invalid string (e.g. `"abc123"` or a non-chain Korean string) → expect INVALID, exit code 1.
   - Test a string `len > 1000` → expect refusal message.
2. Browser: serve with `python -m http.server 8000`, open page, click GENERATE (animated) and 결과 즉시 보기 (instant) — both must show `끝말잇기 검사: 유효 (N단어)` in the new status line; the status resets/updates on each generation.

## Risks / Known Behavior
- Generator can (rarely) produce duplicate words in the chain (no dedup in `pickNext`), which the browser check will flag as invalid — this is the intended "check and display" behavior; do NOT silently fix the generator in this task.
- Standalone Python check can false-negative due to merge ambiguity (see Task 1 limitation).
- No change to git commit/push unless explicitly requested.
