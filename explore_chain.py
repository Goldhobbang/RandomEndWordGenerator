#!/usr/bin/env python3
"""끝말잇기 최대 활용 탐구 v8: 총 시간 예산."""
import collections
import json
import random
import time

WORDS_FILE = "words.json"
MAX_WORD_LEN = 7


def load_words():
    with open(WORDS_FILE, encoding="utf-8") as f:
        return json.load(f)


def build_graph(start_dict):
    seen = set()
    by_start = collections.defaultdict(set)
    for ws in start_dict.values():
        for w in ws:
            seen.add(w)
            by_start[w[0]].add(w)
    by_start = {ch: list(ws) for ch, ws in by_start.items()}
    words = list(seen)
    out_deg = collections.Counter()
    in_deg = collections.Counter()
    for w in words:
        out_deg[w[0]] += 1
        in_deg[w[-1]] += 1
    return words, by_start, out_deg, in_deg


def merged_len(chain):
    if not chain:
        return 0
    total = len(chain[0])
    tail = chain[0][-MAX_WORD_LEN:]
    for w in chain[1:]:
        o = 1
        for k in range(min(MAX_WORD_LEN, len(w)), 0, -1):
            if tail[-k:] == w[:k]:
                o = k
                break
        total += len(w) - o
        tail = (tail + w[o:])[-MAX_WORD_LEN:]
    return total


def trail_search(by_start, start_word, rng, mode):
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
        if mode == "random":
            w = rng.choice(opts)
        elif mode == "survival":
            w = max(opts, key=lambda x: (remaining_out[x[-1]], rng.random()))
        else:
            w = max(opts, key=lambda x: (len(x) * 10 + remaining_out[x[-1]], rng.random()))
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


def run_mode(by_start, unique_words, mode, seconds, seeds):
    best_w = (None, 0)
    best_c = (None, 0)
    rng = random.Random()
    t_end = time.time() + seconds
    iters = 0
    while time.time() < t_end:
        rng.seed(seeds[iters % len(seeds)])
        start_word = rng.choice(unique_words)
        chain = trail_search(by_start, start_word, rng, mode)
        wcnt = len(chain)
        if wcnt > best_w[1]:
            best_w = (chain, wcnt)
        ccnt = merged_len(chain)
        if ccnt > best_c[1]:
            best_c = (chain, ccnt)
        iters += 1
    print(f"[{mode}] 반복 {iters}회, 최장 {best_w[1]}단어 / {best_c[1]}글자", flush=True)
    return best_w, best_c


def main():
    t0 = time.time()
    start_dict = load_words()
    words, by_start, out_deg, in_deg = build_graph(start_dict)
    unique_words = words
    nodes = set(out_deg) | set(in_deg)

    E = len(unique_words)
    print("=" * 60)
    print("끝말잇기 최대 활용 탐구 (unique 기준)")
    print("=" * 60)
    print(f"총 단어 수(unique) : {E}")
    print(f"그래프 노드 수    : {len(nodes)}")
    lengths = sorted(len(w) for w in unique_words)
    print(f"단어 길이: min={lengths[0]} max={lengths[-1]} 평균={sum(lengths)/len(lengths):.2f}")
    print(f"전체 단어 글자 합 : {sum(lengths)} (병합 전 글자 상한)")

    imbalanced = {n: out_deg[n] - in_deg[n] for n in nodes if out_deg[n] != in_deg[n]}
    P = sum(b for b in imbalanced.values() if b > 0)
    N = sum(-b for b in imbalanced.values() if b < 0)
    upper = E - P + 1
    print(f"불균형 노드 수    : {len(imbalanced)} / {len(nodes)}")
    print(f"P={P} N={N}")
    print(f"이론적 최대 단어 상한 : {upper}  (= E - P + 1)")

    print("")
    print("=" * 60)
    print("최장 체인 탐색")
    print("=" * 60)

    results = {}
    results["random"] = run_mode(by_start, unique_words, "random", 15, [1, 2])
    results["survival"] = run_mode(by_start, unique_words, "survival", 60, [11, 22, 33])
    results["chars"] = run_mode(by_start, unique_words, "chars", 60, [44, 55])

    for mode in ("survival", "chars"):
        bw, bc = results[mode]
        wchain, wcnt = bw
        cchain, ccnt = bc
        w2 = try_insert(list(wchain), by_start)
        if len(w2) > wcnt:
            results[mode] = (w2, len(w2)), (cchain, ccnt)
            print(f"[{mode}] 삽입 개선 후 {len(w2)}단어", flush=True)

    for label, mode in (("랜덤", "random"), ("생존", "survival"), ("글자극대", "chars")):
        bw, bc = results[mode]
        wchain, wcnt = bw
        cchain, ccnt = bc
        print("")
        print(f"[{label}] 최장 단어 체인 : {wcnt} 단어 (사용률 {wcnt/E*100:.1f}%)")
        print(f"    병합 문자열 길이 : {merged_len(wchain)} 글자")
        print(f"    최장 글자 체인   : {ccnt} 글자 / {len(cchain)} 단어")

    print("")
    print("=" * 60)
    print("실용 한계 (앱 noLimit: maxWords=10000, maxChars=999999)")
    print("=" * 60)
    print(f"앱 최대 단어 수 : 10000 (사전 이론 최대 {upper}보다 작음)")
    print(f"앱 최대 글자 수 : 10,000단어 병합 기준 약 16,000자 내외")
    print("")
    print(f"총 소요 시간: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()