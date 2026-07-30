# Effect Cleanup Plan: Screen Shake & Screen Flickering

## Scope

Target file: `index.html` (single-page app, EndWord Generator)

Effects that visually escape the central main box (`.container`, max-width 700px):
- **Screen shake**: CSS keyframes + JS classes that apply `transform: translate()` to the entire `#container`, displacing the main box from its normal position
- **Screen flickering**: CSS animations and JS class toggles that create visual instability (color shifting, per-char glitch, slice overlay)

---

## Part 1: Delete Screen Shake Effects

### 1.1 CSS — Remove `@keyframes` blocks (lines 32–61)

Delete the following four `@keyframes` declarations:

| Keyframe | Lines | Description |
|---|---|---|
| `shake-light` | 32–38 | 0.3px micro-translation |
| `shake-medium` | 39–45 | 1px translation |
| `shake-heavy` | 46–54 | 1.5px translation |
| `tremble` | 55–61 | Pseudo-element tremble |

### 1.2 CSS — Remove shake class rules (lines 80–99)

Delete these CSS rules:

- `.container.shake { animation: none; }`
- `#container.shake-light { animation: shake-light 0.12s ease; }`
- `#container.shake-medium { animation: shake-medium 0.18s ease; }`
- `#container.shake-heavy { animation: shake-heavy 0.25s ease; }`
- `#container.shake-light::before { animation: tremble 0.08s infinite alternate; }`
- `#container.shake-medium::before { animation: tremble 0.07s infinite alternate; }`
- `#container.shake-heavy::before { animation: tremble 0.06s infinite alternate; }`

### 1.3 CSS — Remove `.container.shake` rule (line 80)

The `.container.shake { animation: none; }` rule is only needed for shake control and should be removed.

### 1.4 JS — Remove shake functions and related calls

**Lines 454–473**: Remove the entire `/* Screen shake */` block:

```js
/* ?? Screen shake ?? */
const containerEl = document.getElementById('container');
function setShakeLevel(progress) { ... }
function clearShake() { ... }
```

**Important**: `containerEl` is also used by the glitching code in `doGenerate()` (`containerEl.classList.add/remove('glitching')`). After removing the shake block, `containerEl` must be re-declared near its remaining usage in `doGenerate()`, or the `document.getElementById('container')` call should be moved to just before the glitching class toggles.

**Lines 551–552**: Remove `clearShake();` call in `tick()` when `idx >= text.length`.

**Line 564**: Remove `setShakeLevel(idx / text.length);` call in `tick()`.

**Line 575**: Remove `if (navigator.vibrate) navigator.vibrate(10);` call in `tick()`.

**Lines 664–665**: Remove `clearShake();` from the `typeAnimate` callback in `doGenerate()` (first occurrence).

**Lines 681–682**: Remove `clearShake();` from the `typeAnimate` callback in `doGenerate()` (second occurrence).

---

## Part 2: Modify Screen Flickering Effects

The flickering effects are contained within the main box but create visual instability. The plan is to **reduce intensity** rather than fully delete, preserving a subtle visual feedback during typing.

### 2.1 CSS — Modify `#result.typing` rule (lines 150–154)

**Current**:
```css
#result.typing {
    text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
    animation: resultColorShift 0.3s ease infinite alternate;
}
```

**Proposed change**: Remove the color-shift animation and reduce the text-shadow glow to a static, subtle effect:
```css
#result.typing {
    text-shadow: 0 0 4px rgba(255, 255, 255, 0.15);
}
```

### 2.2 CSS — Delete `@keyframes resultColorShift` (lines 155–160)

Delete the entire keyframe block:
```css
@keyframes resultColorShift {
    0% { color: #fff; }
    50% { color: #ffcc00; }
    100% { color: #fff; }
}
```

### 2.3 CSS — Modify `.char.glitch` rule (lines 170, 179)

**Current** (duplicate rule, lines 170 and 179):
```css
#result .char.glitch {
    text-shadow: 2px 0 #ff0040, -2px 0 #00ff80, 0 0 4px rgba(255, 0, 64, 0.4);
}
```

**Proposed change**: Reduce the glitch intensity — smaller offsets, lower opacity:
```css
#result .char.glitch {
    text-shadow: 1px 0 rgba(255, 0, 64, 0.3), -1px 0 rgba(0, 255, 128, 0.3);
}
```

Also remove the duplicate rule (keep only one).

### 2.4 JS — Modify `.char.glitch` toggle in `tick()` (lines 559–560)

**Current**:
```js
if (idx % 2 === 1) {
    span.classList.add('glitch');
    setTimeout(() => span.classList.remove('glitch'), 100 + Math.random() * 150);
}
```

**Proposed change**: Reduce glitch frequency — only apply to every 3rd–4th character, and shorten the duration:
```js
if (idx % 4 === 1) {
    span.classList.add('glitch');
    setTimeout(() => span.classList.remove('glitch'), 60 + Math.random() * 80);
}
```

### 2.5 CSS — Modify `#container.glitching::after` and `@keyframes sliceEffect` (lines 195–210)

**Current**:
```css
#container.glitching::after {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(255, 255, 255, 0.05);
    pointer-events: none;
    z-index: 10;
    animation: sliceEffect 0.15s ease 3;
}
@keyframes sliceEffect {
    0% { transform: translateX(0); opacity: 1; }
    33% { transform: translateX(calc(-100% + 10px)); opacity: 0.6; }
    66% { transform: translateX(calc(100% - 10px)); opacity: 0.8; }
    100% { transform: translateX(0); opacity: 0; }
}
```

**Proposed change**: Reduce overlay opacity and make the animation subtler:
```css
#container.glitching::after {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(255, 255, 255, 0.02);
    pointer-events: none;
    z-index: 10;
    animation: sliceEffect 0.2s ease 2;
}
@keyframes sliceEffect {
    0% { transform: translateX(0); opacity: 0.5; }
    50% { transform: translateX(calc(50% - 5px)); opacity: 0.3; }
    100% { transform: translateX(0); opacity: 0; }
}
```

### 2.6 JS — Modify `glitching` class toggle duration in `doGenerate()` (lines 679–680, 697–698)

**Current**: `setTimeout(() => containerEl.classList.remove('glitching'), 500);`

**Proposed change**: Reduce the glitch overlay duration from 500ms to 300ms:
```js
setTimeout(() => containerEl.classList.remove('glitching'), 300);
```

---

## Part 3: Residual Cleanup

### 3.1 Remove `strip_shake.py`

The `strip_shake.py` script was created to programmatically strip shake effects from `index.html`. After the plan is implemented manually, this script becomes obsolete and should be deleted.

### 3.2 Remove `probe.py`

The `probe.py` script was used to debug the `strip_shake.py` byte-matching logic. It is no longer needed after the plan is executed.

### 3.3 Verify no residual references

After all edits, confirm that the following identifiers no longer appear anywhere in `index.html`:
- `setShakeLevel`
- `clearShake`
- `shake-light`
- `shake-medium`
- `shake-heavy`
- `tremble`
- `navigator.vibrate`
- `@keyframes shake`
- `@keyframes tremble`
- `@keyframes resultColorShift`

---

## Execution Order

1. Delete CSS `@keyframes` blocks (Part 1.1)
2. Delete CSS shake class rules (Part 1.2, 1.3)
3. Modify CSS flickering rules (Part 2.1–2.3)
4. Delete JS shake functions and calls (Part 1.4)
5. Modify JS glitch intensity (Part 2.4)
6. Modify CSS sliceEffect and JS glitching duration (Part 2.5–2.6)
7. Handle `containerEl` declaration relocation (Part 1.4 note)
8. Delete `strip_shake.py` and `probe.py` (Part 3.1–3.2)
9. Verify no residual references (Part 3.3)

---

## Risks

- `containerEl` is referenced in both the removed shake code and the remaining glitching code. The declaration must be preserved and moved to just before its remaining usage in `doGenerate()`.
- The `#container::before` pseudo-element (line 95) is shared by both shake and non-shake code. It should be kept as-is since it's part of the container's visual design (radial gradient overlay), not shake-specific.
- The `resultColorShift` deletion removes the typing color feedback entirely. If some color feedback is desired, a subtler alternative (e.g., a static warm tint) should be added.
- The `navigator.vibrate` removal removes haptic feedback on mobile. If haptic feedback is desired, it should be replaced with a subtler vibration pattern or moved to a different trigger.