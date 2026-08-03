# Custom Word 출현 강도 슬라이더 (가중치 방식)

## Goal
메인페이지(`index.html`)에 **커스텀 단어 출현 강도 슬라이더**를 추가한다. 슬라이더 수치가 높을수록 끝말잇기 체인에 커스텀 단어가 자주 등장한다. **가중치 방식**:
- 슬라이더 = **0** → 커스텀 단어가 아예 등장하지 않음.
- 슬라이더로 만들 수 있는 가중치 값 범위를 **5개로 분할** → 각각 0~20%, 20~40%, 40~60%, 60~80%, 80~100%에 해당하는 비율로 커스텀 단어가 체인에 등장.
- **제약**: 체인 생성 도중 커스텀 단어 삽입이 플레이어가 설정한 **최대 글자수/최대 단어 수를 넘치게 하면 억지로 넣지 않고**, 최대 글자수에 맞춰 정상적으로 종료.

## Current behavior (현재 코드)
- `generateChain(maxWords, maxChars)` (index.html:560-688): `customWords`가 있으면 **"무조건 ≥1개 포함"** 정책 — 중간 삽입 primary(40~60% 지점) + fallback tier 1~4(`findInsertSlot` splice / 끝에 붙이기 / `walkFromSeed` 시드 / [pre, custom] 최소 체인). 모든 삽입에서 `maxChars` 검사는 개별 수행.
- `generateBaseChain` (index.html:471-495): 커스텀 단어 미사용, 단어 수·글자 수 제한 준수.
- 제어 UI: `.controls-wrapper`(index.html:289-304) — 최대 단어 수 / 최대 글자 수 input + `제한 X` 체크박스.
- 커스텀 단어 로드: `localStorage('endword.customWords.v1')` (index.html:855-872).
- 이번 기능은 기존 **"무조건 1개 포함"** 정책을 **대체**한다.

## Design Decisions (설계 결정)
1. **슬라이더**: `<input type="range" id="customWeight" min="0" max="100" step="20" value="0">` + 라벨 텍스트. 위치 6개 = `0(꺼짐)`, `20`, `40`, `60`, `80`, `100` → 밴드 5개(레벨 1~5).
2. **밴드 → 등장 확률 p** (각 단계에서 "커스텀 단어를 시도"할 확률) = 밴드 **중간값**:
   - 꺼짐(0): p = 0
   - 0~20%: p = 0.1 / 20~40%: p = 0.3 / 40~60%: p = 0.5 / 60~80%: p = 0.7 / 80~100%: p = 0.9
   - 목표는 **단어 수 기준 비율**이며, 끝말잇기 연결 제약 때문에 실제 비율은 대략적으로 근사됨(하향 편향 가능).
3. **영속화**: `localStorage('endword.customWeight.v1')`에 저장, `init()`에서 로드. **기본값 0(꺼짐)** — 사용자가 명시적으로 켜야 커스텀 단어가 나옴(기존 "무조건 포함" 동작 제거는 의도된 변경).
4. **커스텀 단어 간 가중치는 동일**: 개별 단어별 가중치 데이터가 없으므로(문자열 리스트) 모든 커스텀 단어는 후보 중 균등 랜덤 선택.
5. **레거시 강제 포함 로직 제거**: weight>0일 때도 "무조건 포함" fallback tier는 쓰지 않음(가중치 확률과 충돌). `findInsertSlot`/`walkFromSeed`는 더 이상 호출되지 않으므로 제거(데드코드 정리).

## New Algorithm

```
function generateChain(maxWords, maxChars) {
    const level = getCustomWeightLevel();          // 슬라이더 0..100 step 20 → 0..5
    if (customWords.length === 0 || level === 0) return generateBaseChain(maxWords, maxChars);
    const p = [0, 0.1, 0.3, 0.5, 0.7, 0.9][level];
    return generateWeightedChain(maxWords, maxChars, p);
}

function generateWeightedChain(maxWords, maxChars, p) {
    const usedWords = [];
    const start = wordList[Math.floor(Math.random() * wordList.length)];
    insertWordSorted(usedWords, start);
    let result = start;
    const chain = [start];

    while (chain.length < maxWords) {                       // maxWords 준수
        const lastChar = result[result.length - 1];
        let next = null;

        if (Math.random() < p) {                            // 확률 p로 커스텀 단어 시도
            const compat = customWords.filter(w =>
                w[0] === lastChar
                && binarySearchWord(usedWords, w) === -1
                && result.length + overlapAppend(result, w).length <= maxChars);  // maxChars 준수
            if (compat.length > 0) next = compat[Math.floor(Math.random() * compat.length)];
        }

        if (!next) {                                        // 실패/미시도 시 정상 단어로 폴백
            const candidates = startDict[lastChar];
            if (!candidates || candidates.length === 0) break;
            next = pickNext(candidates, usedWords);
        }
        if (!next) break;

        const appended = overlapAppend(result, next);
        if (result.length + appended.length > maxChars) break;   // "억지로 넣지 않고 최대 글자수에 맞춰 종료"
        result += appended;
        chain.push(next);
        insertWordSorted(usedWords, next);
    }
    return { text: result, chain };
}
```

**제약 의미 정리**
- `maxWords`: `while` 조건 + 정상 후보 소진 시 `break`.
- `maxChars`: 커스텀 후보 필터와 최종 append 양쪽에서 검사. 커스텀 단어가 글자 수를 넘치면 → 정상 단어로 폴백, 정상 단어도 넘치면 → `break`(체인 종료). **초과 강제 삽입 없음**.

## UI Changes (index.html)
### HTML (`.controls` 내부, index.html:291-298 부근)
```html
<div class="control-group">
    <label>커스텀 출현</label>
    <input type="range" id="customWeight" min="0" max="100" step="20" value="0">
    <span class="weight-label" id="customWeightLabel">꺼짐</span>
</div>
```
### CSS (index.html `<style>`)
- `.control-group input[type="range"] { width: 140px; accent-color: #8a7cc8; }` — 기존 `.control-group input { width: 80px }`(183-194)가 range에 적용되지 않도록 구체성으로 우선.
- `.weight-label { font-size: 0.65rem; color: #777; letter-spacing: 0.05em; }`
### JS
- 전역 상태: `let customWeight = 0;`
- `init()`에서: `localStorage('endword.customWeight.v1')` 로드 → 0..100 정수, 20 단위로 정규화(`Math.round(v/20)*20`). 슬라이더 `value` + 라벨 갱신.
- 슬라이더 `input` 이벤트: `customWeight = +e.target.value` → localStorage 저장 + 라벨 갱신. (생성 시점에 읽으므로 재생성 불필요)
- 헬퍼: `getCustomWeightLevel()`(= customWeight/20), `weightLabel(value)`(라벨 배열), `bandProbability(level)`(=[0,0.1,0.3,0.5,0.7,0.9][level]).
- `generateChain` 본문 교체(560-688) + `generateWeightedChain` 신규 추가.
- `findInsertSlot`(514-536), `walkFromSeed`(538-558) 제거(미사용 데드코드).

## Edge Cases
- `customWords`가 비어 있고 weight>0 → `generateBaseChain` 경로(효과 없음). 필요 시 `info`에 "커스텀 단어 없음(커스텀 단어 →)" 안내 가능(선택).
- 커스텀 단어가 현재 `lastChar`와 안 맞으면 커스텀 시도 실패 → 정상 단어 폴백 (연결 제약으로 실제 비율이 목표보다 낮아질 수 있음).
- 커스텀 단어가 사전 단어와 겹치더라도 `usedWords` 중복 방지는 기존대로 동작.
- 레거시 저장값이 20 단위가 아닐 경우(예: 33) → `Math.round(33/20)*20 = 40`으로 정규화.
- `제한 X`(noLimit) 체크 시 `maxWords=10000/maxChars=999999` → 기존 `generateBaseChain`과 동일하게 후보 소진 시 자연 종료.

## Files to Change
- `index.html` 만 수정. (`custom.html`/README 변경 불필요)

## Implementation Notes (중요)
- `index.html`은 **CRLF**(952 CR / 952 LF, BOM 없음) + `──` 유니코드 주석. `edit` 도구로 직접 수정 시도, **실패하면** 기존 검증된 패턴(임시 Node 스크립트로 ASCII 대상 `replace` 후 `node script.js`, 마지막에 CRLF 복원) 사용.
- 수정 범위:
  1) HTML: `.controls`에 슬라이더 control-group 추가.
  2) CSS: range/weight-label 규칙 추가.
  3) JS: 상태 + 로드/저장 + 슬라이더 이벤트 + 헬퍼 3개.
  4) JS: `generateChain` 본문 교체 + `generateWeightedChain` 추가 + `findInsertSlot`/`walkFromSeed` 제거.
- 편집 후 `<script>` 추출 → `node --check` 문법 검증.

## Validation
1. **Node 시뮬레이션** (wordList fixture + customWords 몇 개 주입):
   - level 0: 수백 회 생성 → **커스텀 단어 0회** 등장.
   - level 1~5 각 수백 회 → 평균 커스텀 단어 비율이 대략 목표 대역 근처인지 측정(연결 제약으로 인한 하향 편향 허용, 상한 초과는 없어야 함).
   - 모든 체인: `validateChain`(연결 규칙·중복) 오류 0건, `text.length <= maxChars`, `chain.length <= maxWords`.
   - maxChars를 작게(예: 10) 설정 → 초과 강제 삽입 없이 제한 안에서 종료.
2. **브라우저 수동**: 슬라이더 0 → 생성 → 커스텀 단어 없음. 100 → 생성 → 커스텀 단어 자주 등장. 슬라이더 중간 값 → 대략 중간 빈도. 새로고침 → 슬라이더 값 유지.
3. **배포** (기존 워크플로우): 커밋 → `git push origin main` → `git push origin main:gh-pages --force`.

## Risks
- 끝말잇기 연결 제약 때문에 실제 커스텀 비율이 목표 밴드보다 낮을 수 있음(특히 커스텀 단어 수가 적을 때). 밴드 중간값 대신 밴드 내 랜덤 `p`를 쓰면 분산이 줄지만 예측성은 중간값이 유리 — 필요 시 조정 가능.
- 기본값 0(꺼짐)으로 설정 시 기존 "무조건 1개 포함" 동작이 사라짐. 사용자가 슬라이더를 켜야 커스텀 단어가 나옴 — **의도된 정책 변경**이며 사용자 확인 필요.
- CRLF 파일 편집 시 줄바꿈 파괴 주의(위 Implementation Notes 참고).

## Implementation Status (2026-08-02, 구현 완료)
- `index.html`에 구현 완료: 슬라이더 UI/CSS, `customWeight` 로드·저장(`endword.customWeight.v1`), `generateWeightedChain` + `generateChain` 교체, `findInsertSlot`/`walkFromSeed` 및 구 fallback tier 제거. CRLF 유지 확인(874/874).
- 검증: `<script>` 추출 `node --check` 통과. Node 시뮬레이션 24/24 — level별 평균 커스텀 비율 0.105/0.300/0.488/0.656/0.821 (목표 0.1/0.3/0.5/0.7/0.9), level 0에서 커스텀 0건, 연결 규칙·중복 오류 0건, maxChars(10)/maxWords(3) 초과 0건.
- 참고: `mergedLen`(index.html:497-512)은 이제 미사용 데드코드 — 후속 정리 대상이지만 동작에 영향 없어 유지함.
