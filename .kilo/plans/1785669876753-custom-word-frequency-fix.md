# 커스텀 단어 출현 빈도 수정 + 연속 슬라이더

## Goal
1. **빈도 수정**: 슬라이더 값과 무관하게 커스텀 단어가 거의 안 나오는 문제를 고쳐, 슬라이더가 높을수록 커스텀 단어가 실제로 자주 등장하도록 한다.
2. **슬라이더 UX**: `step=20` 걸리는 느낌을 없애고 0~100% 연속으로 움직이게 한다. 계산은 기존처럼 5개 밴드(0~20%/20~40%/40~60%/60~80%/80~100%)로만 수행한다.

## Diagnosis (측정 기반, 사용자 확인 완료)
- 현재 `generateWeightedChain`은 매 단계 확률 `p`로 "커스텀 단어 시도"하지만, 체인에 맞는 커스텀 단어(첫 글자 == 현재 끝 글자)가 드물어 대부분 실패 → 정상 단어 폴백.
- 실제 `words.json`(단어 27,831개) + 커스텀 14개로 측정: **슬라이더 100에서도 커스텀 비율 ~4.6%**, 레벨 간 차이 거의 없음.
- 원인 확정: 직접 체인되는 커스텀 단어 부족 → 확률 방식으로는 목표 비율 도달 불가.

## Confirmed Decisions (사용자 확인 완료)
1. **빈도 우선**: 목표 비율에 최대한 근접하도록 브리지 유도 사용. 양수 레벨에서 **최소 1개 보장**. 높은 강도에서 체인이 짧아질 수 있음(사용자 승인).
2. **슬라이더**: `step=1` 연속 0~100. 계산만 밴드 단위 — `level = Math.round(value/20)`, `p = WEIGHT_PROB[level] = [0, 0.1, 0.3, 0.5, 0.7, 0.9][level]`. 라벨은 현재 밴드 텍스트 표시.
3. **최대 글자수/단어 수 제약 유지**: 커스텀 단어 삽입으로 `maxChars`/`maxWords`를 넘치게 하면 억지로 넣지 않고 정상 종료(기존 정책 그대로).
4. 목표 %는 **가능한 최선 근사**(연결 제약 때문에 임의 커스텀 목록으로 80~100%는 비현실적). 측정 기준 커스텀 14개: 레벨별 대략 14/30/35/37/37%.

## Algorithm (generateWeightedChain 교체)
```js
function generateWeightedChain(maxWords, maxChars, p) {
    const used = [];
    const customStarts = new Set(customWords.map(w => w[0]));
    const isLive = w => { const c = w[w.length - 1]; return startDict[c] && startDict[c].length > 0; };

    // 시작 단어 유도: p>0 이면 끝 글자가 커스텀 첫 글자와 맞는 단어로 시작 (커스텀 삽입 부트스트랩)
    let start;
    if (p > 0) {
        const biased = wordList.filter(w => customStarts.has(w[w.length - 1]));
        start = (biased.length > 0 ? biased : wordList)[rand(biased.length > 0 ? biased.length : wordList.length)];
    } else {
        start = wordList[rand(wordList.length)];
    }
    insertWordSorted(used, start);
    let result = start;
    const chain = [start];
    const customRanges = [];
    let customPlaced = 0;

    while (chain.length < maxWords) {
        const lastChar = result[result.length - 1];
        const ratio = chain.length > 0 ? customPlaced / chain.length : 0;
        let next = null;

        if (ratio < p || Math.random() < p) {           // 목표 비율 추적 + 변동성
            // 1) 직접 체인 커스텀
            let compat = customWords.filter(w =>
                w[0] === lastChar
                && binarySearchWord(used, w) === -1
                && result.length + overlapAppend(result, w).length <= maxChars);
            if (compat.length > 0) {
                const live = compat.filter(isLive);
                if (live.length > 0) compat = live;      // 살아있는(이어지는) 커스텀 우선
                next = compat[rand(compat.length)];
            } else {
                // 2) 브리지 유도: 끝 글자가 미사용 커스텀의 첫 글자와 맞는 정상 단어
                const candidates = startDict[lastChar];
                if (candidates) {
                    let pool = candidates.filter(w =>
                        binarySearchWord(used, w) === -1
                        && customStarts.has(w[w.length - 1]));
                    const liveB = pool.filter(isLive);
                    if (liveB.length > 0) pool = liveB;
                    if (pool.length > 0) next = pool[rand(pool.length)];
                }
            }
        }

        if (!next) {                                    // 폴백: 기존 정상 선택
            const candidates = startDict[lastChar];
            if (!candidates || candidates.length === 0) break;
            next = pickNext(candidates, used);
        }
        if (!next) break;

        const appended = overlapAppend(result, next);
        if (result.length + appended.length > maxChars) break;   // 제약 준수, 초과 시 정상 종료

        const startIdx = result.length;
        result += appended;
        const isCustom = customWords.includes(next);
        if (isCustom) {
            customPlaced++;
            customRanges.push({ start: startIdx, end: startIdx + appended.length });  // 하이라이트 유지
        }
        chain.push(next);
        insertWordSorted(used, next);
    }
    return { text: result, chain, customRanges };
}
```
- `generateChain` 디스패치/`generateBaseChain`/하이라이트(`customRanges`→`typeAnimate`/`showResultImmediate`)는 그대로 유지.
- 양수 레벨에서 최소 1개 보장 근거: 시작 단어 유도 + 브리지 유도 → 측정상 `noCustom=0%`.

## UI Changes (index.html)
- HTML: `#customWeight` `step="20"` → `step="1"` (0~100 연속).
- `init()` 로드 정규화 변경: `Math.min(100, Math.max(0, Math.round(raw/20)*20))` → `Math.min(100, Math.max(0, raw))` (연속값 그대로 저장·복원).
- `getCustomWeightLevel()`(`Math.round(customWeight/20)`), `weightLabel()`, `bandProbability()`는 유지(밴드 계산).
- 라벨: 현재 값의 밴드 텍스트 표시 유지(예: value 37 → "20~40%").

## Files to Change
- `index.html` 만 수정. (CRLF 파일 — edit 도구 실패 시 임시 Node 스크립트 방식)

## Validation
1. `<script>` 추출 → `node --check`.
2. 실제 `words.json` 측정(커스텀 14개):
   - 레벨별 비율이 기존(~5%)보다 명확히 상승하고 **단조 증가**: 목표 대략 14/30/35/37/37%.
   - 레벨 0 → 커스텀 0건.
   - 양수 레벨 → 커스텀 ≥1개 (500회 중 0건 이하).
   - 모든 체인: 연결 규칙·중복 오류 0, `text.length <= maxChars`, `chain.length <= maxWords`.
   - `maxChars=10` 소형 테스트 → 초과 0건.
3. 브라우저: 슬라이더 0~100 연속 이동, 라벨 밴드 표시, localStorage 왕복, 노란색 하이라이트 동작.

## Risks
- 높은 강도에서 체인 짧아짐(평균 ~6.5단어, 커스텀 14개 기준) — 사용자 승인된 트레이드오프.
- 빈도 상한은 커스텀 단어 개수·체인 연결성에 의존 — 목록이 적거나 연결성이 낮으면 목표 대비 낮을 수 있음.
- 레벨 3~5 포화(~35~37%)는 임의 목록의 물리적 한계 — 밴드 %는 최선 근사로 문서화.
