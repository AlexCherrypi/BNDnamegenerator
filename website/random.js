// The extra word lists like nsgu-animal or bestimmungswort-food are sorted from
// the best known to the most obscure word, followed by the words that may not
// be shown from them, see generateWords.py. random(list) picks any word of a list,
// random(list, top) one of its top best known words, and random(list, top,
// true) one of the more obscure words after them.
async function random(a, top, obscure) {
    const lenresponse = await fetch('/BNDnamegenerator/words/'+a+'/'+(top === undefined ? 'len' : 'usable')+'.txt')
    if (!lenresponse.ok) throw new Error('Could not load word list '+a)
    const len = Number(await lenresponse.text())
    // files are numbered 0 .. len-1
    let from = 0, to = len
    if (top !== undefined) {
        if (obscure && top < len) from = top
        else to = Math.min(top, len)
    }
    const random = new Uint32Array(1)
    self.crypto.getRandomValues(random);
    const num = from + Math.floor((random[0] / 4294967296) * (to - from))
    const response = await fetch('/BNDnamegenerator/words/'+a+'/'+num+'.txt')
    if (!response.ok) throw new Error('Could not load word '+num+' of '+a)
    const word = await response.text();
    return word
  }

// Which words of a name get something special, set in the URL: ?vulgar or
// ?vulgar=1 sometimes, ?vulgar=2 at least one word, ?vulgar=3 every word.
// The same goes for ?nerd and obscure words.
function marks(flag, words) {
    const value = new URLSearchParams(location.search).get(flag)
    const level = value === null ? 0 : value === '' || isNaN(value) ? 1 : Math.min(3, Math.max(0, Math.round(value)))
    const marked = Array.from({length: words}, () => level === 3 || (level > 0 && Math.random() < 0.2))
    if (level === 2) marked[Math.floor(Math.random() * words)] = true
    return marked
  }

// chooses one of the [word list, top, weight] by weight
function choose(lists) {
    let r = Math.random() * lists.reduce((sum, list) => sum + list[2], 0)
    return lists.find(list => (r -= list[2]) < 0) || lists[lists.length - 1]
  }

// picks a word from one of the [word list, top, weight], an obscure one if asked
async function pick(lists, obscure) {
    const [list, top] = choose(lists)
    return random(list, top, obscure)
  }

// Slurs that two harmless words can make up (Schlitz + Auge) are listed as
// hashes in words/blocked.txt, see generateWords.py. blocked(name) tells if a
// name is one of them, so that the page can pick again.
let blockedHashes
async function blocked(name) {
    if (blockedHashes === undefined) {
        const response = await fetch('/BNDnamegenerator/words/blocked.txt')
        if (!response.ok) throw new Error('Could not load the blocked names')
        blockedHashes = new Set((await response.text()).split('\n'))
    }
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(name.toLowerCase().replace(/[ -]/g, '')))
    const hash = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('').slice(0, 16)
    return blockedHashes.has(hash)
  }
