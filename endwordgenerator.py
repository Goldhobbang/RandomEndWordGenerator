import json
import random

# 끝말잇기 생성 설정
MAX_WORDS = 30           # 생성할 최대 단어 개수
MAX_CHARS = 50           # 생성할 최대 글자 수
WORDS_FILE = "words.json"  # 사전 데이터 파일 경로


def load_words():
    with open(WORDS_FILE, encoding="utf-8") as f:
        start_dict = json.load(f)
    word_list = [word for words in start_dict.values() for word in words]
    return word_list, start_dict


def overlap_append(current, new_word):
    max_overlap = min(len(current), len(new_word))
    for k in range(max_overlap, 0, -1):
        if current.endswith(new_word[:k]):
            return new_word[k:]
    return new_word


def is_one_shot(word, start_dict):
    last_char = word[-1]
    return len(start_dict.get(last_char, [])) == 0


def pick_next(result, candidates, start_dict, remaining):
    non_one_shot = [w for w in candidates if not is_one_shot(w, start_dict)]

    if non_one_shot:
        pool = non_one_shot
    else:
        pool = candidates

    return random.choice(pool)


def generate_chain(word_list, start_dict, max_words=MAX_WORDS, max_chars=MAX_CHARS):
    start = random.choice(word_list)
    result = start
    chain = [start]

    for i in range(max_words - 1):
        last_char = result[-1]
        candidates = start_dict.get(last_char, [])
        if not candidates:
            break

        remaining = max_words - len(chain)
        next_word = pick_next(result, candidates, start_dict, remaining)
        appended = overlap_append(result, next_word)

        if len(result) + len(appended) > max_chars:
            break

        result += appended
        chain.append(next_word)

    return result, chain


def main():
    print("데이터 로딩 중...")
    word_list, start_dict = load_words()
    print(f"단어 {len(word_list)}개 로드 완료")

    result, chain = generate_chain(word_list, start_dict)
    print(f"\n{result}")


if __name__ == "__main__":
    main()
