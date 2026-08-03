const fs = require('fs');
const path = require('path');

const startDict = JSON.parse(fs.readFileSync(path.join(__dirname, 'words.json'), 'utf8'));
const wordList = Object.values(startDict).flat();

function overlapAppend(current, newWord) {
    const maxK = Math.min(current.length, newWord.length);
    for (let k = maxK; k > 0; k--) {
        if (current.endsWith(newWord.slice(0, k))) return newWord.slice(k);
    }
    return newWord;
}
function isOneShot(w) { const c = w[w.length - 1]; return !startDict[c] || startDict[c].length === 0; }
function cmp(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
function bs(arr, w) { let l = 0, h = arr.length - 1; while (l <= h) { const m = (l + h) >> 1; const c = cmp(w, arr[m]); if (c === 0) return m; if (c < 0) h = m - 1; else l = m + 1; } return -1; }
function ins(arr, w) { let l = 0, h = arr.length; while (l < h) { const m = (l + h) >> 1; if (cmp(w, arr[m]) < 0) h = m; else l = m + 1; } arr.splice(l, 0, w); }
function pickNext(c, u) { let p = c.filter(w => !isOneShot(w)); if (p.length === 0) p = c; p = p.filter(w => bs(u, w) === -1); if (p.length === 0) return null; return p[Math.floor(Math.random() * p.length)]; }

function oldGen(customWords, maxWords, maxChars) {
    const usedWords = [];
    const customStarts = new Set(customWords.map(w => w[0]));
    const isLive = w => { const c = w[w.length - 1]; return startDict[c] && startDict[c].length > 0; };
    const start = wordList[Math.floor(Math.random() * wordList.length)];
    ins(usedWords, start);
    let result = start; const chain = [start]; let customPlaced = 0;
    while (chain.length < maxWords) {
        const lastChar = result[result.length - 1];
        const ratio = chain.length > 0 ? customPlaced / chain.length : 0;
        let next = null;
        if (ratio < 0.25 || Math.random() < 0.25) {
            let compat = customWords.filter(w => w[0] === lastChar && bs(usedWords, w) === -1 && result.length + overlapAppend(result, w).length <= maxChars);
            if (compat.length > 0) {
                const live = compat.filter(isLive);
                if (live.length > 0) compat = live;
                next = compat[Math.floor(Math.random() * compat.length)];
            } else {
                const candidates = startDict[lastChar];
                if (candidates) {
                    let pool = candidates.filter(w => bs(usedWords, w) === -1 && customStarts.has(w[w.length - 1]));
                    const liveB = pool.filter(isLive);
                    if (liveB.length > 0) pool = liveB;
                    if (pool.length > 0) next = pool[Math.floor(Math.random() * pool.length)];
                }
            }
        }
        if (!next) { const candidates = startDict[lastChar]; if (!candidates || candidates.length === 0) break; next = pickNext(candidates, usedWords); }
        if (!next) break;
        const appended = overlapAppend(result, next);
        if (result.length + appended.length > maxChars) break;
        result += appended;
        if (customWords.includes(next)) customPlaced++;
        chain.push(next); ins(usedWords, next);
    }
    return { chain, customPlaced };
}

function newGen(customWords, maxWords, maxChars) {
    const usedWords = [];
    const customSet = new Set(customWords);
    const isLive = w => { const c = w[w.length - 1]; return startDict[c] && startDict[c].length > 0; };
    const start = wordList[Math.floor(Math.random() * wordList.length)];
    ins(usedWords, start);
    let result = start; const chain = [start]; let customPlaced = 0;
    while (chain.length < maxWords) {
        const lastChar = result[result.length - 1];
        let next = null;
        if (0.25 > 0 && customSet.size > 0 && Math.random() < 0.25) {
            let compat = customWords.filter(w => w[0] === lastChar && bs(usedWords, w) === -1 && result.length + overlapAppend(result, w).length <= maxChars);
            if (compat.length > 0) {
                const live = compat.filter(isLive);
                if (live.length > 0) compat = live;
                next = compat[Math.floor(Math.random() * compat.length)];
            }
        }
        if (!next) { const candidates = startDict[lastChar]; if (!candidates || candidates.length === 0) break; next = pickNext(candidates, usedWords); }
        if (!next) break;
        const appended = overlapAppend(result, next);
        if (result.length + appended.length > maxChars) break;
        result += appended;
        if (customSet.has(next)) customPlaced++;
        chain.push(next); ins(usedWords, next);
    }
    return { chain, customPlaced };
}

const customs = ['사과', '바나나', '고양이', '강아지', '하늘', '나무', '사람', '시간', '학교', '음악'];
function run(gen) {
    let totC = 0, totL = 0, maxS = 0;
    for (let i = 0; i < 500; i++) {
        const { chain, customPlaced } = gen(customs, 30, 200);
        totC += customPlaced; totL += chain.length;
        const s = chain.length > 0 ? customPlaced / chain.length : 0;
        if (s > maxS) maxS = s;
    }
    return { mean: totC / totL, max: maxS };
}
const oldStats = run(oldGen);
const newStats = run(newGen);
console.log(`OLD mean=${(oldStats.mean * 100).toFixed(2)}% max=${(oldStats.max * 100).toFixed(2)}%`);
console.log(`NEW mean=${(newStats.mean * 100).toFixed(2)}% max=${(newStats.max * 100).toFixed(2)}%`);
console.log(`Target p=0.25 (slider=50%)`);
