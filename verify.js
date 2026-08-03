// Verify EndWord chain generator after fixes.
const fs = require('fs');
const path = require('path');

const startDict = JSON.parse(fs.readFileSync(path.join(__dirname, 'words.json'), 'utf8'));
const wordList = Object.values(startDict).flat();

const MAX_WORD_LEN = 7;

function overlapAppend(current, newWord) {
    const maxK = Math.min(current.length, newWord.length);
    for (let k = maxK; k > 0; k--) {
        if (current.endsWith(newWord.slice(0, k))) return newWord.slice(k);
    }
    return newWord;
}

function isOneShot(word) {
    const lastChar = word[word.length - 1];
    return !startDict[lastChar] || startDict[lastChar].length === 0;
}

function compareWords(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

function binarySearchWord(sortedWords, word) {
    let lo = 0, hi = sortedWords.length - 1;
    while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        const cmp = compareWords(word, sortedWords[mid]);
        if (cmp === 0) return mid;
        if (cmp < 0) hi = mid - 1;
        else lo = mid + 1;
    }
    return -1;
}

function insertWordSorted(sortedWords, word) {
    let lo = 0, hi = sortedWords.length;
    while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (compareWords(word, sortedWords[mid]) < 0) hi = mid;
        else lo = mid + 1;
    }
    sortedWords.splice(lo, 0, word);
}

function pickNext(candidates, usedWords) {
    const nonOneShot = candidates.filter(w => !isOneShot(w));
    let pool = nonOneShot.length > 0 ? nonOneShot : candidates;
    pool = pool.filter(w => binarySearchWord(usedWords, w) === -1);
    if (pool.length === 0) return null;
    return pool[Math.floor(Math.random() * pool.length)];
}

function customProbability(sliderValue) {
    const x = Math.max(0, Math.min(100, sliderValue)) / 100;
    return x * x;
}

function generateWeightedChain(customWords, p, maxWords, maxChars) {
    const usedWords = [];
    const customSet = new Set(customWords);
    const isLive = w => {
        const c = w[w.length - 1];
        return startDict[c] && startDict[c].length > 0;
    };

    let start;
    if (p > 0 && customWords.length > 0) {
        const customStarts = new Set(customWords.map(w => w[0]));
        const biased = wordList.filter(w => customStarts.has(w[w.length - 1]));
        const pool = biased.length > 0 ? biased : wordList;
        start = pool[Math.floor(Math.random() * pool.length)];
    } else {
        start = wordList[Math.floor(Math.random() * wordList.length)];
    }
    insertWordSorted(usedWords, start);
    let result = start;
    const chain = [start];
    let customPlaced = 0;

    while (chain.length < maxWords) {
        const lastChar = result[result.length - 1];
        let next = null;

        if (p > 0 && customSet.size > 0 && Math.random() < p) {
            let compat = customWords.filter(w =>
                w[0] === lastChar
                && binarySearchWord(usedWords, w) === -1
                && result.length + overlapAppend(result, w).length <= maxChars);
            if (compat.length > 0) {
                const live = compat.filter(isLive);
                if (live.length > 0) compat = live;
                next = compat[Math.floor(Math.random() * compat.length)];
            }
        }

        if (!next) {
            const candidates = startDict[lastChar];
            if (!candidates || candidates.length === 0) break;
            next = pickNext(candidates, usedWords);
        }
        if (!next) break;

        const appended = overlapAppend(result, next);
        if (result.length + appended.length > maxChars) break;

        result += appended;
        if (customSet.has(next)) customPlaced++;
        chain.push(next);
        insertWordSorted(usedWords, next);
    }
    return { chain, customPlaced };
}

function validateChain(chain) {
    const errors = [];
    if (chain.length < 2) errors.push('len<2');
    for (let i = 1; i < chain.length; i++) {
        if (chain[i][0] !== chain[i - 1][chain[i - 1].length - 1]) errors.push('link');
    }
    const seen = new Set();
    for (const w of chain) {
        if (seen.has(w)) errors.push('dup');
        seen.add(w);
    }
    return errors;
}

const candidateCustoms = ['사과', '바나나', '고양이', '강아지', '하늘', '나무', '사람', '시간', '학교', '음악'];
const customWords = candidateCustoms.filter(w => startDict[w[0]] && startDict[w[0]].includes(w));
console.log('customs:', customWords);

const sliders = [0, 25, 50, 75, 100];
for (const slider of sliders) {
    const p = customProbability(slider);
    let totalCustom = 0, totalLen = 0, dupCount = 0, linkErr = 0, maxShare = 0;
    const N = 200;
    for (let i = 0; i < N; i++) {
        const { chain, customPlaced } = generateWeightedChain(customWords, p, 30, 200);
        const errs = validateChain(chain);
        if (errs.includes('dup')) dupCount++;
        if (errs.includes('link')) linkErr++;
        totalCustom += customPlaced;
        totalLen += chain.length;
        const share = chain.length > 0 ? customPlaced / chain.length : 0;
        if (share > maxShare) maxShare = share;
    }
    const meanShare = totalCustom / totalLen;
    console.log(
        `slider=${String(slider).padStart(3)}% p=${p.toFixed(3)} ` +
        `meanShare=${(meanShare * 100).toFixed(1)}% ` +
        `maxShare=${(maxShare * 100).toFixed(1)}% ` +
        `dup=${dupCount} linkErr=${linkErr}`
    );
}

const p50 = customProbability(50);
let totalC = 0, totalL = 0, maxS = 0, dup = 0, link = 0;
const N = 500;
for (let i = 0; i < N; i++) {
    const { chain, customPlaced } = generateWeightedChain(customWords, p50, 30, 200);
    const errs = validateChain(chain);
    if (errs.includes('dup')) dup++;
    if (errs.includes('link')) link++;
    totalC += customPlaced;
    totalL += chain.length;
    const s = chain.length > 0 ? customPlaced / chain.length : 0;
    if (s > maxS) maxS = s;
}
const mean = totalC / totalL;
console.log(`\nASSERT slider=50%: mean=${(mean * 100).toFixed(2)}% max=${(maxS * 100).toFixed(2)}% dup=${dup} link=${link}`);
// Correct assertions: gate is an UPPER bound. Mean share must stay ≤ p (0.25).
// Old broken code let share run far above p; new code caps it strictly.
const ok = dup === 0 && link === 0 && mean <= p50 + 0.001 && maxS <= 0.30;
console.log(ok ? 'PASS' : 'FAIL');
process.exit(ok ? 0 : 1);
