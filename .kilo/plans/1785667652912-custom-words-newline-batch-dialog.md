# Custom Words — Newline Batch Detection + Review Dialog

## Goal
`custom.html`의 단어 입력에서 줄바꿈이 포함된 문자열을 **붙여넣으면** 줄바꿈 기준으로 단어를 나눠 "n개의 단어가 감지되었습니다. 추가할까요?" 메시지와 함께 감지된 단어 목록을 모달 창으로 보여준다. 사용자는 목록에서 개별 편집/삭제를 하고, **추가**를 누르면 유효한 단어만 리스트에 추가(중복 제외), **취소**를 누르면 아무것도 추가하지 않고 창을 닫는다.

## Confirmed Decisions (사용자 확인 완료)
1. **감지 시점 = 붙여넣기 시에만**: `<input type="text">`를 `<textarea>`로 교체. textarea `paste` 이벤트 후 값에 줄바꿈으로 구분된 2개 이상의 단어가 있으면 분리 → 모달을 자동 표시. 타이핑 중에는 자동 감지하지 않음(입력은 `autoResize`만). 한 줄이면 기존처럼 제출(추가 버튼 / Ctrl+Enter / Enter) 시 단일 단어 검증 후 바로 추가.
2. **무효/중복 처리 = 유효한 것만 추가 + 요약 메시지**: 모달 목록에는 감지된 줄(빈 줄 제외)을 원래 순서대로 모두 표시. **추가** 시 2글자 이상·공백 없는 단어만 추가하고 중복(배치 내 + 기존 목록)은 제외. 요약 메시지(예: `4개 추가됨, 중복 2개 제외, 잘못된 항목 1개 제외`)를 표시.

## Files to Change
- `custom.html` 만 수정. (`index.html`/`README.md` 불필요)

## Line-ending / Encoding Note
- `custom.html`은 **LF, UTF-8, BOM 없음**으로 확인됨 (`index.html`의 CRLF+`──` 문제 없음). `edit` 도구로 직접 수정해도 됨. 만약 `edit` 실패 시 기존 패턴(임시 Node 스크립트로 ASCII 대상 `replace` 후 `node script.js`, 마지막에 줄바꿈 복원)을 사용.

## Implementation Tasks

### 1. HTML 마크업 변경 (custom.html)
- `.input-row`의 `<input type="text" id="wordInput" maxlength="20">`를 `<textarea id="wordInput" rows="1" placeholder="단어를 입력하고 추가 버튼(또는 Ctrl+Enter)" autocomplete="off"></textarea>` + `<button id="submitBtn" class="btn-sm">추가</button>`로 교체.
  - `maxlength` 제거: index.html 로더는 `length>=2 && !/\s/`만 검사하므로 단일/배치 모두 길이 제한 없이 통일 (단일 경로에서 20자 제한은 조용히 사라짐 — 의도된 동작).
  - textarea 높이는 내용(줄 수)에 따라 자동으로 늘어남(`autoResize()`), 기본은 `rows="1"`.
- `.hint` 문구 보강: "줄바꿈으로 여러 단어를 한 번에 입력할 수 있습니다. Enter=새 줄, Ctrl+Enter 또는 추가 버튼=제출."
- `</div>`(`.container`) 직전에 모달 추가:
  ```html
  <div class="modal-overlay" id="modalOverlay" hidden>
    <div class="modal">
      <h2>단어 감지</h2>
      <p class="modal-msg" id="modalMsg"></p>
      <ul class="list" id="modalList"></ul>
      <div class="modal-actions">
        <button class="btn" id="modalAdd">추가</button>
        <button class="btn ghost" id="modalCancel">취소</button>
      </div>
    </div>
  </div>
  ```

### 2. CSS 추가 (custom.html `<style>`)
- `.input-row textarea`: 기존 `.input-row input` 스타일과 동일(배경/보더/radius), `line-height: 1.4; resize: none; overflow: hidden;`(커스텀 리사이즈·스크롤바 제거), `font-family: inherit;`. 높이는 JS `autoResize()`가 `scrollHeight`로 설정(내용 줄 수에 따라 유연하게, 기본은 한 줄, 상한 없음 — 붙여넣기 시 모달이 바로 열리므로 과도하게 커질 일이 없음).
- `.input-row`에 `align-items: flex-start` 추가 (textarea가 늘어나도 추가 버튼은 첫 줄에 정렬).
- `.modal-overlay`: `position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; z-index: 100;` (`[hidden]{display:none}` 기본으로 충분).
- `.modal`: 기존 `.container` 스타일 모방(보더/반투명 배경/backdrop-blur/radius), `width: min(560px, 92vw); max-height: 80vh; display: flex; flex-direction: column; padding: 1.5rem;`.
- `#modalList`: `overflow-y: auto; min-height: 0;` (항목이 많을 때 스크롤).
- `.modal-actions`: 우측 정렬(flex, gap).
- `.btn`: `.btn-sm`을 확장한 기본 버튼 스타일(`padding: 0.55rem 1.4rem;`), `.btn.ghost`는 투명하게, hover 시 기존 보더 컬러 규칙 재사용.
- `.error.ok { color: #6c8; }` — 성공/요약 메시지용.

### 3. JS 로직 (custom.html `<script>`)
- 새 상태: `let detectedWords = [];` (모달 내 작업용 복사본), `let modalEditingWord = null;`, `const $submitBtn`, `$modalOverlay`, `$modalMsg`, `$modalList`, `$modalAdd`, `$modalCancel` 참조 추가.
- **`submitInput()`** (신규):
  1. `$wordInput.value`를 `/\r?\n/`로 분리 → 각 줄 `trim()` → 빈 줄 제거 → `words`.
  2. `words.length === 0` → `showError('단어를 입력하세요.')` 후 return.
  3. `words.length === 1` → 기존 `validateWord(words[0])` 경로로 바로 추가(기존 `addWord` 로직 재사용, 입력 클리어 + focus + render).
  4. `words.length >= 2` → `detectedWords = words.slice();` → `openModal()`.
- **`openModal()`**: `modalMsg.textContent = `${detectedWords.length}개의 단어가 감지되었습니다. 추가할까요?`;` `modalEditingWord = null;` overlay `hidden` 해제, `renderModalList()`, `$modalAdd.focus()`.
- **`closeModal(clearInput)`)**: overlay `hidden` 설정, `detectedWords = []; modalEditingWord = null;` clearInput이면 `$wordInput.value = ''` 후 `$wordInput.focus()`.
- **`renderModalList()`**: `detectedWords`를 `.item` 마크업으로 렌더 — 기존 메인 리스트와 동일 패턴(단어 텍스트 + 편집 시 input + `저장`/`취소`, 비편집 시 `편집`/`삭제` 버튼). `data-act`/`data-index`(배열 인덱스) 사용. 편집 상태는 `modalEditingWord`(문자열) 대신 `modalEditingIndex`(숫자)가 안전 — 중복 문자열 구분.
- **모달 이벤트** (이벤트 위임, `#modalList`):
  - `edit` → `modalEditingIndex = idx; renderModalList();` 후 `requestAnimationFrame`으로 `#medit-{idx}` focus/select.
  - `del` → `detectedWords.splice(idx, 1); renderModalList();` (0개면 목록 빈 상태 표시).
  - `save`/`cancel` → 편집 input 값 반영/취소 후 `modalEditingIndex = null; renderModalList();`
  - 모달 편집 input의 keydown: Enter=저장, Escape=취소 (메인 리스트 패턴 재사용).
- **`$modalAdd` click → `commitDetected()`**:
  1. 유효성 검사: 각 단어 `trim()`, 빈 값 skip, `length < 2` 또는 `/\s/` → `invalid++`.
  2. 중복 검사: `Set`(배치 내) + `customWords.includes` → `dup++`.
  3. 유효·비중복 단어를 `customWords`에 push → 기존 정렬(`localeCompare('ko')`) → `saveCustomWords()` → `render()`.
  4. `closeModal(true)` 후 요약 표시: `added>0`이면 `showNotice(\`${added}개 추가됨${dup?', 중복 '+dup+'개 제외':''}${invalid?', 잘못된 항목 '+invalid+'개 제외':''}\`)`, 모두 제외됐으면 `showNotice('추가된 단어가 없습니다 (모두 중복이거나 잘못된 항목)')`. `showError`와 동일한 타이머 오토클리어(`showNotice` 신규, `.error.ok` 스타일).
  4-0. `detectedWords`가 빈 배열이면 → `closeModal(true)` + `showError('추가할 단어가 없습니다.')`.
- **`$modalCancel` click / overlay Esc / overlay 배경 클릭** → `closeModal(true)` (추가 취소 + 입력 클리어로 재트리거 방지).
- **붙여넣기 감지** (`$wordInput` `paste` 이벤트 → `requestAnimationFrame(detectInput)`):
  - 붙여넣기 직후 값에 2개 이상의 비어있지 않은 줄이 있으면 `detectedWords = words; openModal()` (붙여넣기 시에만 자동, 타이핑 중에는 감지 안 함).
  - 모달이 이미 열려 있으면 무시(`if (!$modalOverlay.hidden) return;`) — 오버레이가 textarea 입력을 막으므로 중복 재렌더 방지.
  - `input` 이벤트는 `autoResize` 전용(감지 없음). `compositionend` 후에는 `autoResize`만 실행.
  - 제출 경로(`submitInput`)의 멀티라인 분기도 방어적으로 유지.
- **`autoResize()`**: `style.height = 'auto'` 후 `scrollHeight + 'px'`로 설정. `input` 이벤트마다 호출(IME 조합 중에도), `compositionend` 후, `addWord()`/`closeModal(true)`로 입력이 비워질 때, 초기 로드 시 호출 — 내용 줄 수에 따라 높이가 늘었다 줄어듦.
- **`$wordInput` keydown**:
  - `e.isComposing || e.keyCode === 229` → return (IME 조합 중 제출 방지).
  - `Enter && !e.shiftKey && !$wordInput.value.includes('\n')` → `preventDefault(); submitInput();` (한 줄 입력 시 기존 'Enter=바로 추가' 보존)
  - `(e.ctrlKey || e.metaKey) && e.key === 'Enter'` → `preventDefault(); submitInput();` (멀티라인 제출)
  - 그 외 Enter는 textarea 기본(줄바꿈) 동작.
- **`$submitBtn` click** → `submitInput()`.
- 기존 `$wordInput`의 Enter keydown 리스너는 위 로직으로 대체. `addWord()`는 `submitInput()`의 단일 단어 경로에서 호출되도록 유지.

### 4. 주의/엣지 케이스
- CRLF 붙여넣기(`\r\n`) 대비 `/\r?\n/` 분리.
- 빈 줄·공백만 있는 줄은 분리 시 제거.
- 배치 내 중복(같은 단어 두 줄)은 추가 시 1회만 삽입.
- 모달 편집 중 메인 리스트의 `editingWord`와 상태가 섞이지 않도록 별도 `modalEditingIndex` 사용.
- 모달 열림 상태에서 메인 리스트는 오버레이에 가려 클릭 불가(추가 조치 불필요).
- `hidden` 속성 토글로 표시/숨김.

## Validation
1. **문법**: `custom.html`에서 `<script>` 추출 → `node --check` 통과.
2. **Node/수동 시나리오** (브라우저):
   - 한 단어 입력 + Enter → 기존처럼 즉시 추가, 모달 안 뜸.
   - "사과\n배\n포도" 붙여넣기 → 추가 버튼 없이 **즉시** "3개의 단어가 감지되었습니다. 추가할까요?" + 3개 목록.
   - 목록에서 1개 삭제, 1개 편집 → 추가 → 저장된 목록에 반영, 중복(기존 항목과 겹치는 단어) 제외, 요약 메시지 표시.
   - 이미 있는 단어만 붙여넣기 → 추가 시 "추가된 단어가 없습니다" 안내.
   - 취소 → 창 닫힘, 입력창 비워짐, 기존 목록 불변.
   - 새로고침 후 localStorage 유지.
3. **index.html 회귀**: 커스텀 단어가 정상 로드되는지 1회 확인(코드 변경 없으므로 우선순위 낮음).
4. **배포** (기존 워크플로우): 커밋 → `git push origin main` → `git push origin main:gh-pages --force`.

## Risks
- textarea 전환으로 `maxlength=20` 제한이 사라짐(단일/배치 모두) — index.html 로더와 동일 규칙(≥2자, 공백 없음)으로 통일하므로 기능상 문제 없음.
- "Enter=바로 추가"는 한 줄 입력일 때만 유지되고, 줄바꿈이 이미 있는 값에서는 Enter가 줄바꿈을 추가 — 사용자가 확인한 "붙여넣기 시 감지" 정책과 일치.
