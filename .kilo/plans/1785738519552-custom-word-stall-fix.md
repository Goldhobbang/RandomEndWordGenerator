# 커스텀 단어 스톨 수정 (Unreachable Customs가 세션 전체 정지 유발)

## Context
- 현재 플랜 `1785688267012-custom-word-even-rotation.md` 구현 완료(working tree, 미커밋).
- 사용자 보고: "어느정도 잘 나오다가 여러번 생성할 수록 전체 커스텀 단어 출현 빈도가 0에 가까워진다. 새로고침해야 해결된다."
- 사용자 확인 사항: localhost, **모든 슬라이더 값 동일**, **제한 유무 무관**, 슬라이더 중간 변경 무효, **새로고침만 해결**.

## Diagnosis (실측, 현재 working tree 코드 기준)
- 14개 전부 도달 가능한 단어 리스트: 100,000회 생성까지 비율/균등 완전 안정 (p=1.0 → 15.5%, 단어별 20,345/20,346). 재현 안 됨.
- **65개 혼합 리스트**(8개 = 첫 글자가 어떤 사전 단어의 끝 글자에도 없는 단어 포함)에서 재현:
  - 비율 창: `0.05% → 0.02% → 0.01% → 0.00%` (50,000회, 5,000 단위 창) — **사용자 증상과 정확히 일치**.
  - 커스텀 없는 체인 99.97%, 단어별 0회 8개.
- **근본 원인 (확정)**:
  1. 시작 단어는 항상 사전 단어이고, `lastChar`는 항상 어떤 단어의 끝 글자가 되어야 함. 첫 글자가 사전 단어들의 끝 글자 집합에 **없는** 커스텀은 `w[0] === lastChar`가 성립할 수 없어 **어떤 알고리즘으로도 배치 불가능** (물리적 한계; 구버전 x²/band도 동일).
  2. 엄격한 due-gate(`usage <= target`)는 최소 단계(min-tier) 단어만 배치 허용. 회전 라운드가 "배치 불가 단어가 유일한 최소 단계"인 상태에 도달하면:
     - 어떤 단어도 배치 불가 → `customPlacedTotal` 정지 → `target` 고정 → `dueSet` 영구 고정 → **세션 전체 영구 스톨 (0개)**.
     - 새로고침(= 카운터 초기화)만 해결. 슬라이더/제한은 카운터와 무관하므로 영향 없음 — 사용자 보고와 완전 일치.
- 혼합 리스트에서 첫 라운드(~20체인) 만에 스톨하므로 "처음엔 잘 나오다가" 현상과 일치.

## Fix (인라인 검증 완료)
회전(due-gate) 대상을 **도달 가능한 커스텀으로 한정**. 도달 불가 단어는 목록에 남되 회전 계산에서 제외 (그대로 배치 불가 = 물리적 한계, 기존보다 악화 없음).

`index.html` 수정 (3곳):
1. 모듈 상태 (`customUsage`/`customPlacedTotal` 선언 근처, ~line 415):
   ```js
   let customEndChars = new Set();
   ```
2. `init()`에서 `wordList = Object.values(startDict).flat();` 이후 (~line 880):
   ```js
   customEndChars = new Set(wordList.map(w => w[w.length - 1]));
   ```
3. `generateWeightedChain` 시작부 (~line 632, `customStarts` 정의 다음):
   ```js
   // 도달 가능 커스텀만 회전 대상 (첫 글자가 사전 끝 글자인 단어)
   const customReachable = customEndChars.size > 0
       ? customWords.filter(w => customEndChars.has(w[0]))
       : customWords;
   const target = customPlacedTotal / (customReachable.length || 1);              // 누적 평균
   const dueWords = customReachable.filter(c => (customUsage[c] || 0) <= target); // 평균 이하 = 배치 예정
   const dueSet = new Set(dueWords);
   const dueStarts = new Set(dueWords.map(w => w[0]));
   ```
   그 외 나머지(direct due-gate, bridge, start bias, 최소 사용 선택, 카운터 갱신)는 **변경 없음**.
   - `customSet`/`customStarts`는 전체 `customWords` 기준 유지 (브리지/폴백 경로).
   - `customReachable`이 빈 경우(`customEndChars` 미초기화 또는 전부 도달 불가): dueSet 공집합 → 배치 없음(도달 불가 단어는 어차피 배치 불가) → 스톨 아님.
   - 카운터 갱신은 기존 그대로(배치된 커스텀만 증가; 도달 불가 단어는 배치되지 않으므로 0 유지).

## Validation
1. `<script>` 추출 → `node --check`.
2. 실측 하네스 (DOM 스텁 + 실제 `words.json`, N=50,000):
   - **14개 전부 도달 가능 리스트 (회귀)**: p=1.0/0.49/0.25에서 비율 15.5%/6.5%/2.7% 안정, 단어별 maxDev ≤ 5%, 100,000회 창 단위로 스톨 없음.
   - **65개 혼합 리스트 (재현 방지)**: p=1.0 → 비율 ~15.5%로 안정(창 단위 15.5±0.1%), 커스텀 없는 체인 0% (p=1.0), 도달 가능 단어 균등 (maxDev ≤ 5%), 도달 불가 단어 0회(예상).
   - 레벨 0: 커스텀 0건.
   - 연결 오류·중복 0건, `text.length ≤ maxChars`, `chain.length ≤ maxWords`, `customRanges` 정렬 검증, `maxChars=10` 초과 0건.
3. 브라우저: 커스텀 목록에 도달 불가 단어(예: 핫초코, 마카롱) 포함해 배치 추가 → 슬라이더 100에서 연속 생성 → 커스텀이 계속 등장(스톨 없음), 도달 불가 단어는 등장하지 않음(예상 동작), 새로고침 없이도 유지.

## Known Limits / Follow-ups (선택)
- 도달 불가 커스텀은 어떤 알고리즘에서도 등장할 수 없음 (끝말잇기 연결 규칙상 물리적 한계). 이번 수정의 목표는 "전체 빈도 스톨 제거"이며, 해당 단어 개별 출현은 불가.
- (선택 후속) `custom.html` 추가/배치 검증에서 첫 글자가 사전 끝 글자 집합에 없으면 경고/거부 → 사용자 혼란 방지.

## Files to Change
- `index.html` 만 수정 (모듈 변수 1줄 + init 1줄 + `generateWeightedChain` 4줄 교체). CRLF 유지 — 수정 후 LF-only 라인 발생 시 전체 `\r?\n` → `\r\n` 정규화로 복구.
- `custom.html` 등 다른 파일은 건드리지 않음.

## Open Questions
- 없음 (원인 측정 확인, 수정 인라인 검증 완료). 배포는 구현 완료 후 기존 flow(커밋/푸시/gh-pages) 사용.
