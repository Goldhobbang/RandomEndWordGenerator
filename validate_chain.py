#!/usr/bin/env python3
"""Validate Korean word chain (끝말잇기) merged strings.

A string S is considered a valid 끝말잇기 string if there exists a sequence
of 2 or more distinct dictionary words w1..wn such that:

  1. w1 matches S from position 0 (w1 is a prefix of S).
  2. For each i > 1: w_i starts with the last character of w_{i-1}
     (the chaining rule), and w_i is merged onto S by overlapping the
     previous word's tail with the same overlap_append semantics as the
     generator (overlap of at least 1 character).
  3. The merged text equals S exactly.

Known limitation: because the generator merges overlapping parts, the merged
string can be ambiguous. Some chains (e.g. where an appended word is fully
hidden inside earlier text) cannot be reconstructed from the string alone and
will be reported INVALID even though they were produced from a valid chain.
The in-browser check (which has the actual word chain) is exact.

Usage:
    python validate_chain.py "<string>" [words.json path]
Exit codes: 0 = valid, 1 = invalid, 2 = usage/IO error.
"""
import json
import sys

MAX_LEN = 1000          # refuse strings longer than this
NODE_BUDGET = 200_000   # backtracking node budget
MAX_WORDS = 2000        # max words in a recovered chain


def load_dict(path="words.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_index(start_dict):
    """Return (word_set, by_first) where by_first maps first char -> words
    sorted longest-first."""
    word_set = set()
    by_first = {}
    for words in start_dict.values():
        for w in words:
            if not w:
                continue
            word_set.add(w)
            by_first.setdefault(w[0], []).append(w)
    for bucket in by_first.values():
        bucket.sort(key=len, reverse=True)
    return word_set, by_first


def validate_string(s, start_dict):
    """Return (is_valid, segmentation, errors)."""
    if len(s) < 2:
        return False, [], ["문자열이 너무 짧아 끝말잇기로 검증할 수 없습니다 (2자 이상 필요)"]
    if len(s) > MAX_LEN:
        return False, [], [f"문자열이 너무 길어 검증 불가 ({len(s)}자, 최대 {MAX_LEN}자)"]

    _, by_first = build_index(start_dict)
    n = len(s)
    state = {"nodes": 0, "budget_exceeded": False}

    def dfs(pos, prev_word, used, words):
        if pos == n:
            return len(words) >= 2
        if len(words) >= MAX_WORDS:
            return False
        state["nodes"] += 1
        if state["nodes"] > NODE_BUDGET:
            state["budget_exceeded"] = True
            return False

        prev_last = prev_word[-1]
        for w in by_first.get(prev_last, ()):
            if w in used:
                continue
            max_o = min(len(prev_word), len(w))
            for o in range(max_o, 0, -1):
                if prev_word[-o:] != w[:o]:
                    continue
                tail = w[o:]
                if pos + len(tail) > n or s[pos:pos + len(tail)] != tail:
                    continue
                words.append(w)
                used.add(w)
                if dfs(pos + len(tail), w, used, words):
                    return True
                used.discard(w)
                words.pop()
        return False

    # First word must be a prefix of S (bucket by S[0]).
    for w in by_first.get(s[0], ()):
        if s.startswith(w):
            seg = [w]
            used = {w}
            if dfs(len(w), w, used, seg):
                return True, list(seg), []
    if state["budget_exceeded"]:
        return False, [], ["검증 시도 횟수 초과 (문자열이 복잡하여 탐색이 중단됨)"]
    return False, [], [
        "문자열을 사전 단어들로 재구성할 수 없습니다 "
        "(겹침 병합으로 인해 실제 생성 체인과 다르게 판정될 수 있음)"
    ]


def main(argv):
    if not argv:
        print("Usage: python validate_chain.py \"<string>\" [words.json path]")
        return 2
    s = argv[0]
    dict_path = argv[1] if len(argv) > 1 else "words.json"
    try:
        start_dict = load_dict(dict_path)
    except FileNotFoundError:
        print(f"ERROR: 사전 파일을 찾을 수 없습니다: {dict_path}")
        return 2
    except json.JSONDecodeError as e:
        print(f"ERROR: 사전 파일 파싱 실패: {e}")
        return 2

    ok, segmentation, errors = validate_string(s, start_dict)
    if ok:
        print("VALID:", " / ".join(segmentation))
        return 0
    print("INVALID:")
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
