# -*- coding: utf-8 -*-
"""이론상 최장 끝말잇기 체인 생성 + validate.py 검증.

- 생존 휴리스틱(목적지 잔여 출차 우선) + 사이클 삽입으로 최장 체인 탐색
- 최장 병합 문자열을 콘솔과 longest_chain.txt에 출력
- validate.py의 validate_chain()으로 사전/연결/중복/병합 재구성 검증
"""
import collections
import json
import random
import sys
import time

import validate

WORDS_FILE = "words.json"
OUT_FILE = "longest_chain.txt"
MAX_WORD_LEN = 7


def build_graph(start_dict):
    seen = set()
    by_start = collections.defaultdict(set)
    for ws in start_dict.values():
        for w in ws:
            seen.add(w)
            by_start[w[0]].add(w)
    by_start = {ch: list(ws) for ch, ws in by_start.items()}
    return list(seen), by_start


def merged_text(chain):
    if not chain:
        return ""
    parts = [chain[0]]
    tail = chain[0][-MAX_WORD_LEN:]
    for w in chain[1:]:
        o = 1
        for k in range(min(MAX_WORD_LEN, len(w)), 0, -1):
            if tail[-k:] == w[:k]:
                o = k
                break
        parts.append(w[o:])
        tail = (tail + w[o:])[-MAX_WORD_LEN:]
    return "".join(parts)


def trail_search(by_start, start_word, rng):
    """생존 휴리스틱: 목적지 글자의 잔여 출차가 큰 단어 우선."""
    used = set()
    remaining_out = collections.Counter({ch: len(ws) for ch, ws in by_start.items()})
    chain = [start_word]
    used.add(start_word)
    remaining_out[start_word[0]] -= 1
    cur = start_word[-1]
    while True:
        opts = [w for w in by_start.get(cur, []) if w not in used]
        if not opts:
            break
        w = max(opts, key=lambda x: (remaining_out[x[-1]], rng.random()))
        used.add(w)
        remaining_out[w[0]] -= 1
        chain.append(w)
        cur = w[-1]
    return chain


def try_insert(chain, by_start):
    """사이클 삽입: 매 삽입마다 pos_map 재구축해 연결 규칙 보장."""
    used = set(chain)
    rng = random.Random(7)
    inserted = 0
    while inserted < 30:
        pos_map = collections.defaultdict(list)
        for i in range(len(chain) - 1):
            pos_map[(chain[i][-1], chain[i + 1][0])].append(i)
        cands = [w for ws in by_start.values() for w in ws if w not in used]
        rng.shuffle(cands)
        placed = False
        for w in cands:
            positions = pos_map.get((w[0], w[-1]))
            if not positions:
                continue
            i = positions[0]
            chain.insert(i + 1, w)
            used.add(w)
            inserted += 1
            placed = True
            break
        if not placed:
            break
    return chain


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    t0 = time.time()
    start_dict = json.load(open(WORDS_FILE, encoding="utf-8"))
    words, by_start = build_graph(start_dict)
    E = len(words)

    print("최장 체인 탐색 중 (생존 휴리스틱, 최대 60초)...", flush=True)
    best = (None, 0)
    rng = random.Random()
    seeds = [11, 22, 33, 44, 55]
    t_end = time.time() + 60
    iters = 0
    while time.time() < t_end:
        rng.seed(seeds[iters % len(seeds)])
        start_word = rng.choice(words)
        chain = trail_search(by_start, start_word, rng)
        if len(chain) > best[1]:
            best = (chain, len(chain))
        iters += 1

    chain, wcnt = best
    chain = try_insert(chain, by_start)
    wcnt = len(chain)
    merged = merged_text(chain)
    ccnt = len(merged)

    print(f"반복 {iters}회 완료 ({time.time()-t0:.1f}s)")
    print(f"최장 체인: {wcnt} 단어 / {ccnt} 글자 (단어 사용률 {wcnt/E*100:.1f}%)")
    print(f"이론 상한: {E}단어 중 트레일 상한 E-P+1")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(merged)
    print(f"병합 문자열 저장 완료: {OUT_FILE} ({ccnt}자)")

    print("")
    print("병합 문자열 (전체):")
    print(merged)

    print("")
    print("단어 목록 앞/뒤:")
    print("  시작:", " / ".join(chain[:10]), "...")
    print("  끝  :", "...", " / ".join(chain[-10:]))

    # validate.py 검증
    print("")
    print("=" * 50)
    print("validate.py 검증")
    print("=" * 50)
    errors = validate.validate_chain(merged, chain)
    if errors:
        print("ERRORS FOUND:")
        for e in errors[:20]:
            print(" -", e)
        if len(errors) > 20:
            print(f"   ... 외 {len(errors) - 20}건")
    else:
        print("VALID: 유효한 끝말잇기 체인입니다")
        print(f"(사전 포함 {wcnt}단어, 연결 규칙 OK, 중복 없음, 병합 재구성 일치)")
    print(f"총 소요 시간: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()