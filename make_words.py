import json
import os
import glob


JSON_DIR = "json"
OUTPUT_FILE = "words.json"
MIN_WORD_LENGTH = 2


def extract_nouns():
    words = []
    for filepath in sorted(glob.glob(os.path.join(JSON_DIR, "*.json"))):
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        entries = data["LexicalResource"]["Lexicon"]["LexicalEntry"]
        for entry in entries:
            lemma = entry.get("Lemma", {})
            if isinstance(lemma, list):
                lemma = lemma[0] if lemma else {}
            feat = lemma.get("feat", {})
            if isinstance(feat, list):
                feat = feat[0] if feat else {}
            if isinstance(feat, dict):
                word = feat.get("val", "")
            else:
                continue

            if len(word) < MIN_WORD_LENGTH:
                continue

            pos = None
            pos_feats = entry.get("feat", [])
            if isinstance(pos_feats, dict):
                pos_feats = [pos_feats]
            elif not isinstance(pos_feats, list):
                pos_feats = []
            for item in pos_feats:
                if isinstance(item, dict) and item.get("att") == "partOfSpeech":
                    pos = item.get("val")
                    break

            if pos != "명사":
                continue

            words.append(word)
    return words


def group_by_first_char(words):
    groups = {}
    for word in words:
        first = word[0]
        if first not in groups:
            groups[first] = []
        groups[first].append(word)
    for key in groups:
        groups[key] = sorted(set(groups[key]))
    return dict(sorted(groups.items()))


def main():
    print("JSON 파일에서 명사 추출 중...")
    words = extract_nouns()
    print(f"추출된 명사: {len(words)}개")

    print("첫 글자별 그룹핑 및 정렬 중...")
    groups = group_by_first_char(words)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)

    print(f"{OUTPUT_FILE} 저장 완료 ({os.path.getsize(OUTPUT_FILE) / 1024:.1f}KB)")


if __name__ == "__main__":
    main()
