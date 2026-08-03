# 커스텀 단어 균등 출현 (Even Rotation) + 알고리즘 점검

## Goal
1. **모든 커스텀 단어가 고루 등장**: 어느 특정 단어가 지배하지 않고, 전체 커스텀 단어가 균등하게 회전 (측정 기준 편차 ~0%).
2. **슬라이더는 여전히 전체 커스텀 빈도 조절**: 값이 높을수록 커스텀이 자주 나오되, 나올 때마다 균등 회전.
3. 전체 생성 알고리즘 점검 결과를 계획에 문서화.

## Diagnosis (실측, 현재 working tree 기준)
- **현재 working tree의 알고리즘은 x² 커브 버전**(`customProbability` + 단계별 compat 시도 + 바이어스 시작). 커밋된 HEAD(a2adc40)의 브리지 유도 버전과 다르며, 사용자가 되돌려 놓은 상태임. 이 계획은 **현재 working tree 버전을 기준으로** 수정한다.
- 실측 (실제 `words.json` 27,831개 + 커스텀 14개, 3,000회, 슬라이더 100):
  - 커스텀 분포: 자두잼 1,873회, 수박씨 721, 체리파이 335, … 멜론아이스 3, 딸기우유 32 → **최대 편차 426%**.
  - **근본 원인**: 커스텀은 "체인 현재 끝 글자 == 커스텀 첫 글자"일 때만 배치됨. 사전 체인의 끝 글자 분포가 크게 치우쳐 있어(자/키/수 등 흔한 끝글자), 그 글자에 대응하는 커스텀은 매번 강제 배치됨. 반대로 멜/딸/두 같은 희귀 첫 글자 커스텀은 거의 도달 불가.
  - 강제 후속 단어 증폭: 자두잼→잼잼(잼으로 시작하는 사전 단어가 극소수)으로 최상위 단어가 더 부풀려짐.
- 사전 자체 문제는 없음: 중복 엔트리 0개, `wordList`/`startDict` 일치.
- 기본 체인의 사전 단어 반복(류머티즘 0.23%)은 희귀 첫글자 문자의 후보 풀이 1~2개라 구조적으로 발생하는 것으로 **사용자 명시에 따라 이번 범위 제외** (정도가 약함, 최상위 0.2% 수준).

## Confirmed Decisions (사용자 확인 완료)
1. **균등 우선**: 엄격한 due-gate 방식으로 모든 커스텀 단어 균등 회전 (maxDev ~0%). 대가: 슬라이더 100 기준 커스텀 비율 ~37% → **~15%** (체인당 ~3개, 단어별 균등). 사용자 승인.
2. **세션 내 유지**: 균등 회전 카운터는 메모리(in-memory)에만 저장. 새로고침 시 초기화. localStorage 저장하지 않음.

## Algorithm (generateWeightedChain 내부 교체 — 프로토타입 검증 완료)
기존 유지: `customProbability` x² 커브, `generateChain` 디스패치, `pickNext`, `generateBaseChain`, `validateChain`, 하이라이트(`customRanges` → `typeAnimate`/`showResultImmediate`), 최대 글자/단어 제약.

모듈 레벨 상태 추가 (`customWeight` 선언 근처):
```js
let customUsage = {};        // 커스텀 단어 -> 세션 내 배치 횟수
let customPlacedTotal = 0;   // 세션 내 커스텀 배치 총합
```

`generateWeightedChain(maxWords, maxChars, p)` 내부 (현재 working tree 버전 기준 교체):
```js
const usedWords = [];
const customSet = new Set(customWords);
const isLive = w => { const c = w[w.length - 1]; return startDict[c] && startDict[c].length > 0; };
const customStarts = new Set(customWords.map(w => w[0]));
const target = customPlacedTotal / (customWords.length || 1);              // 누적 평균
const dueSet  = new Set(customWords.filter(c => (customUsage[c] || 0) <= target));  // 평균 이하 = 배치 예정

// 시작 유도: due 커스텀의 첫 글자로 끝나는 사전 단어로 시작
let start;
if (p > 0 && customWords.length > 0) {
    let biased = wordList.filter(w => dueSet.size > 0 ? dueSet.has(w[w.length - 1]) : customStarts.has(w[w.length - 1]));
    if (biased.length === 0) biased = wordList.filter(w => customStarts.has(w[w.length - 1]));
    start = biased.length > 0
        ? biased[Math.floor(Math.random() * biased.length)]
        : wordList[Math.floor(Math.random() * wordList.length)];
} else {
    start = wordList[Math.floor(Math.random() * wordList.length)];
}

while (chain.length < maxWords) {
    const lastChar = result[result.length - 1];
    let next = null;

    if (p > 0 && customSet.size > 0 && Math.random() < p) {
        const compat = customWords.filter(w =>
            w[0] === lastChar
            && binarySearchWord(usedWords, w) === -1
            && result.length + overlapAppend(result, w).length <= maxChars);
        const dueCompat = compat.filter(w => dueSet.has(w));                // 1) 직접 체인: due만 선택
        if (dueCompat.length > 0) {
            const live = dueCompat.filter(isLive);
            const pool = live.length > 0 ? live : dueCompat;
            let min = Infinity, best = [];
            for (const w of pool) { const u = customUsage[w] || 0; if (u < min) { min = u; best = [w]; } else if (u === min) best.push(w); }
            next = best[Math.floor(Math.random() * best.length)];           // 최소 사용 단어 선택 (균등 회전)
        } else {
            const candidates = startDict[lastChar];                         // 2) 브리지: due 커스텀 첫 글자로 끝나는 사전 단어
            if (candidates) {
                let pool = candidates.filter(w =>
                    binarySearchWord(usedWords, w) === -1
                    && (dueSet.size > 0 ? dueSet.has(w[w.length - 1]) : customStarts.has(w[w.length - 1])));
                const liveB = pool.filter(isLive);
                if (liveB.length > 0) pool = liveB;
                if (pool.length > 0) next = pool[Math.floor(Math.random() * pool.length)];
            }
        }
    }

    if (!next) {                                                            // 3) 폴백: 기존 정상 선택
        const candidates = startDict[lastChar];
        if (!candidates || candidates.length === 0) break;
        next = pickNext(candidates, usedWords);
    }
    if (!next) break;

    const appended = overlapAppend(result, next);
    if (result.length + appended.length > maxChars) break;

    const startIdx = result.length;
    result += appended;
    if (customSet.has(next)) {
        customPlaced++;
        customRanges.push({ start: startIdx, end: startIdx + appended.length });
    }
    chain.push(next);
    insertWordSorted(usedWords, next);
}

// 세션 균등 카운터 갱신
for (const w of chain) if (customSet.has(w)) { customUsage[w] = (customUsage[w] || 0) + 1; customPlacedTotal++; }
return { text: result, chain, customRanges };
```

동작 원리 (검증된 메커니즘):
- `due`(평균 이하) 커스텀만 배치 + 최소 사용 단어 선택 + due 방향 시작/브리지 유도 → 모든 커스텀이 평균으로 수렴 (maxDev ~0%).
- 슬라이더는 `p`를 낮춰 전체 배치 빈도를 줄일 뿐, 균등 회전은 모든 p에서 유지.
- 검증된 수치: p=1.0 → 비율 15.6%, 단어별 min/max 610/611; p=0.7 → 10.4%, 465/466; p=0.5 → 6.7%, 329/330.

## Files to Change
- `index.html` 만 수정 (script 내 `generateWeightedChain` 교체 + 모듈 상태 2줄 추가). CRLF 유지 — 수정 후 LF-only 라인 발생 시 전체 `\r?\n` → `\r\n` 정규화로 복구.

## Validation
1. `<script>` 추출 → `node --check`.
2. 실측 하네스 (DOM 스텁 + 실제 `words.json` + 커스텀 14개, N=3000):
   - 슬라이더 100/70/50/0 (`customProbability` 매핑 1.0/0.49/0.25/0)에서 단어별 배치 수 **maxDev ≤ 5%** (양수 레벨).
   - 레벨 0: 커스텀 0건.
   - 연결 오류·중복 0건, `text.length ≤ maxChars`, `chain.length ≤ maxWords`.
   - `customRanges` 정렬: 각 range의 `text.slice(start,end)` == 해당 커스텀 단어의 비겹침 접미사.
   - `maxChars=10` 소형 테스트: 초과 0건.
3. 브라우저: 슬라이더 100에서 연속 생성 → 커스텀 단어가 돌아가며 균등 등장, 슬라이더 값에 따라 전체 빈도 변화, 노란 하이라이트 정상.

## Risks
- 슬라이더 100 커스텀 비율 ~15%로 하락 (사용자 승인). 체인당 평균 커스텀 ~3개, 전 체인에 커스텀 존재.
- 첫 글자가 어떤 사전 단어의 끝 글자와도 맞지 않는 커스텀은 브리지/시작 유도로도 도달 불가 → 자연 흐름에서만 등장 (엣지 케이스; 현재 코드보다 악화되지는 않음).
- 균등 카운터는 새로고침 시 초기화 (사용자 승인). 커스텀 목록이 세션 중 바뀌는 경로는 없음(init에서만 로드).
- 기본 체인 사전 단어 반복(류머티즘 등 ~0.2%)은 구조적 특성으로 이번 범위 제외 — 원하면 후속 작업으로 사전 단어 다양화 가능.
