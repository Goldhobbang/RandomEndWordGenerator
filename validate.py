# -*- coding: utf-8 -*-
"""끝말잇기 체인 검증 (validate.py)

- validate_chain(input_str, segmentation): 병합 문자열과 단어 분할을 검증
  * 사전 포함 여부
  * 연결 규칙 (다음 단어 첫 글자 == 이전 단어 마지막 글자)
  * 중복 단어
  * 겹침 병합 재구성 (분할을 overlap_append로 병합한 결과 == input_str)
- 직접 실행 시 기존 예제 검증 출력
"""
import json

with open("words.json", encoding="utf-8") as f:
    start_dict = json.load(f)

word_list = [word for words in start_dict.values() for word in words]
word_set = set(word_list)

MAX_WORD_LEN = 7  # 사전 최대 단어 길이


def overlap_append(current, new_word):
    max_overlap = min(len(current), len(new_word))
    for k in range(max_overlap, 0, -1):
        if current.endswith(new_word[:k]):
            return new_word[k:]
    return new_word


def validate_chain(input_str, segmentation):
    """(errors) 반환. errors가 비어 있으면 유효."""
    errors = []

    if not segmentation:
        return ["분할이 비어 있습니다"]

    # 1) 겹침 병합 재구성 == input_str
    merged = ""
    tail = ""
    for w in segmentation:
        if not merged:
            merged = w
            tail = w[-MAX_WORD_LEN:]
        else:
            o = 1
            for k in range(min(MAX_WORD_LEN, len(w)), 0, -1):
                if tail[-k:] == w[:k]:
                    o = k
                    break
            merged += w[o:]
            tail = (tail + w[o:])[-MAX_WORD_LEN:]
    if merged != input_str:
        errors.append(
            f"병합 재구성 불일치 (기대 {len(input_str)}자, 실제 {len(merged)}자)"
        )

    # 2) 단어별: 길이 2 이상, 사전 포함
    for i, word in enumerate(segmentation):
        if len(word) < 2:
            errors.append(f"Word {i+1} '{word}': too short (1 syllable)")
        if word not in word_set:
            errors.append(f"Word {i+1} '{word}': not in dictionary")

    # 3) 연결 규칙
    for i in range(1, len(segmentation)):
        prev_last = segmentation[i - 1][-1]
        curr_first = segmentation[i][0]
        if prev_last != curr_first:
            errors.append(
                f"Chain break: '{segmentation[i-1]}'(ends:{prev_last}) "
                f"-> '{segmentation[i]}'(starts:{curr_first})"
            )

    # 4) 중복 단어
    seen = set()
    for word in segmentation:
        if word in seen:
            errors.append(f"Duplicate: '{word}'")
        seen.add(word)

    return errors


if __name__ == "__main__":
    # 기존 진단 예제 (그대로 유지)
    s = "물레방아동복병아리색채"
    seg = ["물레", "방아", "동복", "병아리", "색채"]
    print("Input:", s)
    print("Segmentation:", " / ".join(seg))
    errs = validate_chain(s, seg)
    if errs:
        print("ERRORS FOUND:")
        for e in errs:
            print(e)
    else:
        print("VALID chain!")