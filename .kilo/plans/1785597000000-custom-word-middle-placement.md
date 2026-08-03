# Custom Word Middle Placement Plan

## Goal
현재 `index.html`의 단어 생성 알고리즘에서 커스텀 단어가 **항상 체인 맨 앞**에 나오는 문제를 고쳐, 커스텀 단어가 **체인 중간(40~60% 지점)**에 나타나도록 알고리즘을 수정한다. 동시에 "커스텀 단어 1개 **무조건 포함**" 요구사항은 유지한다.

## Diagnosis (현재 코드)
- `generateChain` (index.html:560-604) 은 2단계로 동작:
  1. **Phase 1 — splice**: `findInsertSlot` (index.html:514-536) 이 `chain[i][-1]==w[0]` **그리고** `w[-1]==chain[i+1][0]` **둘 다** 맞는 자리를 찾아 커스텀 단어를 중간에 끼움. 조건이 매우 까다로워 짧은 체인에서는 대부분 실패.
  2. **Phase 2 — seed**: `walkFromSeed` (index.html:538-558) 가 커스텀 단어를 체인의 **첫 단어**로 삼고 진행. 성공률이 높아 항상 여기까지 오게 됨.
- 따라서 커스텀 단어가 항상 맨 앞에 노출되는 현상이 발생.

## New Algorithm Design

### Primary — Mid-injection (기본 경로)
`generateChain(maxWords, maxChars)` (커스텀 단어 존재 시) 를 다음 로직으로 대체:

```
retry up to 30 times:
    targetMid = max(1, floor(maxWords * (0.4 + Math.random() * 0.2)))   # 40~60% 창
    usedWords = []; start = wordList 랜덤 (기존과 동일)
    chain = [start]; result = start; injected = false

    while chain.length < maxWords:
        lastChar = result[-1]
        if (!injected && chain.length >= targetMid):
            compat = customWords.filter(w =>
                w[0] == lastChar
                && binarySearchWord(usedWords, w) == -1
                && result.length + overlapAppend(result, w).length <= maxChars)
            if compat.length > 0:
                w = compat[랜덤]
                append w (result += overlapAppend(result, w); chain.push(w); insertWordSorted(usedWords, w))
                injected = true
                continue
        next = pickNext(startDict[lastChar], usedWords)   # 기존 정상 후보 선택
        if !next: break
        append next (기존 방식)
    if injected && chain.length >= 2:
        return { text: result, chain }
```

- 삽입 전에 최소 `targetMid` 단어를 쌓으므로 커스텀 단어는 맨 앞이 아닌 **중간**에 위치.
- 현재 `lastChar`로 시작하는 커스텀 단어가 없으면 정상 단어로 계속 진행 → 삽입 지점이 자연스럽게 뒤로 밀림 (슬라이딩).
- 체인이 삽입 전에 끊기면 새 랜덤 체인으로 재시도.

### Fallback tiers (무조건 포함 보장, 사용자 확인됨)
30회 재시도 후에도 중간 삽입 실패 시, 기존 함수를 아래 우선순위로 재사용:

1. **중간 splice**: 기존 `findInsertSlot` + `mergedLen <= maxChars` (index.html:566-587 로직 유지) — 양끝이 맞으면 중간 배치.
2. **끝에 붙이기 (신규)**: base chain 생성 후, `base.chain[마지막][-1] == w[0]` 이고 `w` 미사용이며 `maxChars` 이내인 커스텀 단어 `w`를 체인 끝에 append. (맨 앞 아님)
3. **맨 앞 시드 (최후): 기존 `walkFromSeed`** — 어떤 경우에도 커스텀 단어 1개 포함 보장. (드문 경우)

### Constraints / edge cases
- 커스텀 단어는 후보 풀(startDict/wordList)에 들어가지 않으므로 정상 후보로는 나타나지 않고, **삽입으로 1회만** 사용됨 → 중복 사용 없음. (usedWords에 insertWordSorted로 기록, 단일 injected 플래그)
- `maxChars` 체크: 삽입·끝붙이기 시 `result.length + appended.length <= maxChars` 검사.
- `customWords.length === 0` → 기존 `generateBaseChain` 그대로.
- `showChainStatus`/`validateChain`는 사전 포함 검사가 없으므로 커스텀 단어 포함 체인도 정상 동작 (연결 규칙·중복만 검사).

## Files to Change
- `index.html` 만 수정. (`custom.html` 완성 상태 유지, README는 이미 기능 문서화 — 중간 배치 문구는 선택적으로 한 줄 보강)

## Implementation Notes (중요)
- `index.html`은 **CRLF** + 유니코드 `──` 주석 사용. 기존에 검증된 방식(임시 Node 스크립트로 ASCII 대상 replace 후 `node --check`)으로 수정할 것.
- 수정 범위: `generateChain` 함수 본문 (index.html:560-604) 교체. `findInsertSlot`, `walkFromSeed`, `generateBaseChain`, `pickNext`, `overlapAppend`, `insertWordSorted`, `binarySearchWord`, `mergedLen`은 재사용(보존).
- 편집 후 `<script>` 추출 → `node --check` 문법 검증.

## Validation
1. **Node 해리스 테스트**: customWords 몇 개 주입 후 수백 회 생성하여:
   - 모든 체인에 커스텀 단어 ≥1개 포함 (무조건 보장)
   - 대부분의 체인에서 커스텀 단어가 index 0이 아님 (중간 배치)
   - 인접 단어 연결 규칙 위반 0건
   - 중복 단어 0건
2. **브라우저 수동 확인**: custom.html에서 단어 추가 → 메인에서 생성 → 커스텀 단어가 중간에 등장하는지 확인.
3. **배포** (기존 워크플로우): 커밋 → `git push origin main` → `git push origin main:gh-pages --force`.

## Risks
- 드문 글자(예: 쌍자음 초성)로 시작하는 커스텀 단어는 중간 접점이 없어 Fallback tier 2/3으로 내려갈 수 있음 — 이는 사용자가 승인한 "무조건 포함 우선" 정책의 의도된 동작.
- 커스텀 단어가 매우 적거나 전부 같은 첫 글자면 삽입 위치가 편향될 수 있으나, retry로 완화됨.
