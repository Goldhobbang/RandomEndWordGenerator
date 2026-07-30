# index.html 전투 이펙트 업그레이드 계획

## 목표
현재 은은한 UI를 **화려하고 전투적인 비주얼**로 업그레이드한다. 생성 순간의 임팩트를 극대화하는 데 집중한다.

## 디자인 방향
- **비주얼 키워드**: 격정적, 폭발적, 임팩트 중심
- **원칙**: 이펙트가 결과 텍스트의 가독성을 방해하지 않도록 한다. 모든 이펙트는 `pointer-events: none`이거나 임시 요소여야 한다.
- **아웃오브범위**: 사운드 효과, 스캔라인 토글 체크박스, 성능 프로파일링 도구

## 현재 이펙트 (기준선)
| 이펙트 | 구현 방식 | 강도 |
|--------|-----------|------|
| 배경 드리프트 | CSS `::before` radial-gradient + animation | ★☆☆ |
| 화면 흔들림 | CSS `@keyframes screenShake` ±1px / 150ms | ★☆☆ |
| 글자 팝인 | `.char` span scale+blur animation / 300ms | ★★☆ |
| 파티클 | Canvas 6색, 중력+감소 / 6개/글자 | ★☆☆ |
| 진동 | `navigator.vibrate(10)` | ★☆☆ |
| 제목 그라데이션 | CSS `background-position` animation | ★★☆ |

## 변경 사항

### P0 — 강화된 화면 흔들림 (CSS + JS)
**현행**: 고정 `±1px`, `0.15s`, `@keyframes screenShake`
**변경**: 강도를 생성 진행 상황에 비례시키는 JS 제어
- **약한 흔들림** (`shake-light`): `±1px`, 80ms — 첫 5글자
- **중간 흔들림** (`shake-medium`): `±3px`, 120ms — 6~15글자  
- **강한 흔들림** (`shake-heavy`): `±5px`, 200ms — 16글자+
- **구현**: JS에서 `shake` counter를 관리, 클래스를 동적 변경
- **CSS**: `@keyframes shake-light`, `shake-medium`, `shake-heavy` 각각 정의
- **고주파 떨림 레이어**: `#container`에 `::before` pseudo-element를 추가하여 CSS-only `@keyframes`로 고주파 진동 (transform: translateX(±0.5px)을 8ms 주기로 교대) — JS rAF 불필요

### P0 — 임팩트 플래시 + 경계 광 (CSS + JS)
**화면 플래시**: 단어가 추가될 때 `position: fixed` 오버레이가 `opacity 0→0.12→0`으로 70ms 펄스
- **HTML 변경**: `<body>` 맨 안에 `<div id="flashOverlay" class="flash-overlay">` 추가 (영구 요소, JS에서 show/hide 제어)
- **CSS**: `@keyframes flashPulse { 0%{opacity:0} 30%{opacity:0.12} 100%{opacity:0} }`
- **JS 트리거**: `doGenerate` 호출 시 1회만 `flashOverlay.classList.add('flash')` → 70ms 후 `remove`
**경계 광**: 플래시와 동시에 `#container`에 `box-shadow: 0 0 40px rgba(138,124,200,0.5)`를 400ms 동안 적용, 그 후 400ms transition으로 페이드아웃
- JS에서 `classList.add('glow')` 후 `setTimeout`으로 `classList.remove('glow')` 호출
- **트리거**: `typeAnimate` 시작 시 1회만 발동

### P1 — 파티스템 강화 (JS)
**파티클 타입 구분** (기존 단일 유형 → 3유형):
| 타입 | 속도 | 수명 | 크기 | 용도 |
|------|-------|------|------|------|
| Spark | 기본×2 | 0.12 | 1~2px | 빠른 점멸, 중심발사 |
| Ember | 기본×0.5 (상승) | 0.6 | 2~4px | 따뜻한 위로 떠오름 |
| Debris | 기본×0.3 (중력강) | 0.8 | 3~7px | 느린 잔해 낙하 |

**버스트 패턴**: 중심점에서 `cos/sin` 기반 360° 분산 발사 (현재는 순수 랜덤 각도)
**밀도**: 기본 6개 → 체인 길이 비례 → 최대 18개 (캡)
**색상**: 기존 6색 + `#ff4444`, `#ffaa00`, `#ff00ff` → 총 9색 (전투적 빨강/주황 강조)

### P1 — 텍스트 임팩트 (JS + CSS)
**임팩트 줌**: 단어 추가 시 `#result`에 `scale(1.04)` → `scale(1)`로 120ms 트랜지션
**색변화**: 생성 중 텍스트 색이 `#fff → #ffcc00 → #fff`를 순환 (CSS `animation` 또는 JS interval)
**글로우**: 결과 텍스트에 `text-shadow: 0 0 8px rgba(255,255,255,0.3)`을 애니메이션 활성화 시에만 적용

### P2 — 글리치 이펙트 (JS + CSS)
**텍스트 RGB 스플릿**: 생성 중 홀수 번 째 `.char` span에 `text-shadow`로 색상 오프셋
- `text-shadow: 2px 0 #ff0040, -2px 0 #00ff80, 0 0 4px rgba(255,0,64,0.4)`
- 각 글자마다 80~250ms 무작위 지속, 한 번만 적용 후 제거
**컨테이너 슬라이싱**: 버튼 클릭 시 `#container`에 임시 `::after` 슬라이스 효과 2~3회 재생 → 200ms 후 제거
- JS에서 생성 시점에 `containerEl.classList.add('slicing')` → CSS `@keyframes slice` 실행 → `setTimeout`으로 `remove`
- `::after`는 CSS에서 `position: absolute`, `top:0; left:0; width:100%; height:100%; background: rgba(255,255,255,0.06); pointer-events:none` 정의, `@keyframes slice`가 `translateX`를 무작위로 3회 이동 후 `opacity:0`

### P2 — 타이핑 리듬 변형 (JS)
**간격 변동**: 고정 30ms → 12~60ms 무작위
- **스트터**: 중간 구간(체인 길이 50% 지점)에서 2번 연속 30ms 후 다음 글자 → 텀블링 효과
- **터미네이션**: 마지막 4글자는 8ms 간격으로 가속
- 글자 간 간격 자체를 JS에서 `setTimeout` 변수로 제어
- **동시 생성 방지**: 새 클릭 시 `animTimer` clear + 기존 상태 초기화 (기존 코드에 이미 `if (animTimer) clearTimeout(animTimer)` 존재)

### P3 — 결과 전환 애니메이션 (JS)
**슬라이드아웃→슬라이드인**: 기존 텍스트 `translateX(-100%) + fade-out` → 80ms 대기 → 새 텍스트 `translateX(100%) → translateX(0) + fade-in`
- CSS `transition`으로 처리, JS에서 클래스 토글

## 변경하지 않는 항목
- `words.json` 로드 로직 및 데이터 구조 — 변경 불가
- 끝말잇기 알고리즘 (overlapAppend, isOneShot, pickNext, generateChain) — 순수 로직이므로 변경 금지
- `make_words.py` 및 Python 백엔드 — 이펙트 업그레이드와 무관
- HTML 구조의 기존 컨트롤 요소 (input, checkbox, button) — 기존 속성 및 이벤트 유지

## 구현 순서
1. 강화된 화면 흔들림 (P0) — CSS keyframes 3종 + JS 클래스 토글
2. 임팩트 플래시 (P0) — DOM 오버레이 요소 추가 + CSS 애니메이션
3. 파티스템 강화 (P1) — JS 파티클 타입 분기 + 버스트 패턴
4. 텍스트 임팩트 (P1) — `#result` 트랜지션 + color-shift
5. 글리치 이펙트 (P2) — per-character text-shadow + container slice
6. 타이핑 리듬 (P2) — interval 변동 + 스트터/터미네이션 로직
7. 결과 전환 (P3) — slide-out/in 트랜지션

## 주의사항 및 제약
- **`result-wrap` 중복 CSS**: 라인 58~64와 84~87이 중복 정의됨 — 이펙트 추가 시 올바른 규칙만 유지
- **성능**: 파티클 수 캡(최대 18/글자), Canvas 레이아웃 `will-change: contents` 고려
- **`noLimit` 체크**: 제한 해제 시 maxWords=10000이므로 파티클 밀도·흔들림 강도가 과도할 수 있음 → 파티클 수와 흔들림 강도를 자체 캡 (maxParticles=18, maxShakeIntensity=1.0)
- **`prefers-reduced-motion`**: 이 사용자 설정이 활성화되면 모든 모션 효과를 최소 수준으로 축소 (shake=0, particles=0, animation=none)
- **CORS**: `fetch('words.json')` 로컬 서버 필요
- **중복 요소**: `result-wrap` 클래스가 2번 정의되어 있어 혼란 방지를 위해 통합 권장

## 검증 방법
1. 브라우저에서 `index.html` 직접 열기 (local server 필수)
2. GENERATE 버튼 반복 클릭 — 흔들림 강도 변화 확인
3. 긴 결과(40자+)와 짧은 결과(10자 미만)로 강도 차이 확인
4. `noLimit` 체크 시 이펙트가 과도해지지 않는지 확인
5. `prefers-reduced-motion` 시뮬레이션으로 모든 이펙트 정지 확인
6. 파티클 수와 타입 분포가 예상대로 작동하는지 확인
7. 생성 중 반복 클릭 시 이전 애니메이션이 정상 중단되는지 확인
8. 결과 텍스트가 완전히 읽힐 수 있는지 (이펙트가 가려지지 않는지) 확인
