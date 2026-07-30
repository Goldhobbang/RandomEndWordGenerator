import json

with open("words.json", encoding="utf-8") as f:
    start_dict = json.load(f)

word_list = [word for words in start_dict.values() for word in words]
word_set = set(word_list)

def validate_chain(input_str, segmentation):
    print("Input:", input_str)
    print("Segmentation:", " / ".join(segmentation))
    print(f"Concat check: {''.join(segmentation)} == {input_str}: {''.join(segmentation) == input_str}")
    print()

    errors = []
    for i, word in enumerate(segmentation):
        # Check 2+ syllables
        if len(word) < 2:
            errors.append(f"  Word {i+1} '{word}': too short (1 syllable)")
        # Check standard noun (exists in dict)
        if word not in word_set:
            errors.append(f"  Word {i+1} '{word}': not in dictionary")
        # Check chain rule
        if i > 0:
            prev_last = segmentation[i-1][-1]
            curr_first = word[0]
            if prev_last != curr_first:
                errors.append(f"  Chain break: '{segmentation[i-1]}'(ends:{prev_last}) -> '{word}'(starts:{curr_first})")

    if errors:
        print("ERRORS FOUND:")
        for e in errors:
            print(e)
    else:
        print("VALID chain!")
    print()

# The example string
s = "물레방아동복병아리색채"

# Attempt 1: 물레 / 방아 / 동복 / 병아리 / 색채
validate_chain(s, ["물레", "방아", "동복", "병아리", "색채"])

# Attempt 2: Try to find valid chain that produces this merged string
# water wheel -> gear -> ...
print("=== Checking if any valid chain can produce this merged string ===")
print("Merged string:", s)
print()

# Let's trace what overlap_append would do if we try different word sequences
def overlap_append(current, new_word):
    max_overlap = min(len(current), len(new_word))
    for k in range(max_overlap, 0, -1):
        if current.endswith(new_word[:k]):
            return new_word[k:]
    return new_word

# Try: water wheel -> what starts with le?
print("Words ending with '물' (to start chain with):")
start_words = [w for w in word_set if w[-1] == '물' and len(w) >= 2]
print(start_words[:10])

# Try chain starting with water wheel (물레)
print("\nWords starting with '레' (after water wheel):")
le_words = start_dict.get('레', [])
print(le_words[:10])

# Check '방아' specifically
print("\nIs '방아' in dictionary:", "방아" in word_set)
# Find what words end with 방 (so 방아 can follow)
bang_words = [w for w in word_list if w.endswith('방') and len(w) >= 2]
print("Words ending with '방' (to connect to 방아):", bang_words[:10])

# Check connection: 동복 -> 병아리
print("\nWords ending with 동 (to connect to 동복):", [w for w in word_list if w.endswith('동') and len(w) >= 2][:10])
print("Words starting with 복 (to follow 동복):", start_dict.get('복', [])[:10])
print("Words starting with 병 (to connect 병아리 correctly):", start_dict.get('병', [])[:10])
