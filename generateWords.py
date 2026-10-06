from defusedxml.ElementTree import fromstring
import datetime
import gzip
import requests
import random
import os
import re
from fugen import Fugen
from wordinfo import HURTFUL_WORDS, Entry, Synset, WordInfo, blocked, english_meanings, lists

startingDir = './website/words/'
DC = '{https://globalwordnet.github.io/schemas/dc/}'


def download(url):
    print("Downloading from '"+ url +"'")
    response = requests.get(url, timeout=600)
    response.raise_for_status()
    print("Download from '"+ url +"' finished")
    return response.content


def findEnglishUrl():
    # The asset name contains the release year, which is not necessarily the current year,
    # so look up the actual file name of the latest release.
    try:
        release = requests.get('https://api.github.com/repos/globalwordnet/english-wordnet/releases/latest', timeout=60)
        release.raise_for_status()
        for asset in release.json()['assets']:
            if re.fullmatch(r'english-wordnet-\d{4}\.xml\.gz', asset['name']):
                return asset['browser_download_url']
        print("No matching asset found in latest release, probing years instead")
    except requests.RequestException as e:
        print("Could not query latest release ("+str(e)+"), probing years instead")
    # Fallback: try the last few years, newest first
    for year in range(datetime.date.today().year, datetime.date.today().year - 6, -1):
        candidate = 'https://github.com/globalwordnet/english-wordnet/releases/latest/download/english-wordnet-'+str(year)+'.xml.gz'
        if requests.head(candidate, allow_redirects=True, timeout=60).ok:
            return candidate
    raise RuntimeError("Could not find an English WordNet download")


def writeList(key, wordList, usable=None):
    os.makedirs(startingDir+key, exist_ok=True)
    print("Generating files for key '"+key+"' in '"+os.path.abspath(startingDir+key)+"'...")
    pos = 0
    for word in wordList:
        with open(startingDir+key+'/'+str(pos)+'.txt', 'w', encoding="utf-8") as f:
            f.write(word)
        pos = pos + 1
    with open(startingDir+key+'/len.txt', 'w') as f:
            f.write(str(pos))
    if usable is not None:
        # the first words are fit to show, the rest are slurs, plurals and the like
        with open(startingDir+key+'/usable.txt', 'w') as f:
                f.write(str(usable))


print("Parsing xml ...")
root = fromstring(download('https://raw.githubusercontent.com/hdaSprachtechnologie/odenet/master/odenet/wordnet/deWordNet.xml'))
print("Reading words and meanings ...")
synsets = dict()
for synset in root.iter('Synset'):
    texts = [element.text or '' for element in synset if element.tag in ('Definition', 'Example')]
    synsets[synset.get('id')] = Synset(synset.get('ili'), synset.get(DC+'subject'), ' '.join(texts),
                                       [(relation.get('relType'), relation.get('target')) for relation in synset.iter('SynsetRelation')])
entries = list()
for entry in root.iter('LexicalEntry'):
    lemma = entry.find('Lemma')
    entries.append(Entry(lemma.get('writtenForm'), lemma.get('partOfSpeech'), entry.get(DC+'description') or '',
                         entry.get(DC+'type') == 'Basiswortschatz', [sense.get('synset') for sense in entry.iter('Sense')]))
del root

print("Finding and sorting words ...")
words = dict()
for entry in entries:
    word = entry.word
    if not word.isdigit() and not any(e in word for e in ['.',',','/','\\',')','(']) and len(word) > 2:
        for key in lists(word, entry.pos):
            words.setdefault(key, set())
            words[key].add(word)

# The first word of a name gets its linking element already attached
# (Sonne -> Sonnen, Zeitung -> Zeitungs), see fugen.py
print("Choosing linking elements ...")
fugen = Fugen(words['nsgu'])
words['bestimmungswort'] = set()
firstParts = dict()
reasons = dict()
for noun in words['nsgu']:
    decision = fugen.decide(noun)
    reason = decision[1] if decision else 'left out'
    reasons[reason] = reasons.get(reason, 0) + 1
    if decision:
        firstParts[noun] = decision[0].apply(noun)
        words['bestimmungswort'].add(firstParts[noun])
print("Linking elements by "+ str(reasons) +", for example:")
for noun in random.sample(sorted(words['nsgu']), 20):
    print("  "+ fugen.explain(noun))

# OdeNet links its meanings to the English WordNet, which knows the main
# meaning and the category of a word much better, see wordinfo.py
print("Decompressing English WordNet ...")
root = fromstring(gzip.decompress(download(findEnglishUrl())).decode("utf-8"))
print("Reading English meanings ...")
english = english_meanings(
    {synset.get('id'): (synset.get('ili'), synset.get('lexfile'),
                        ' '.join(element.text or '' for element in synset if element.tag in ('Definition', 'Example')),
                        synset.get('members', '').split(),
                        [(relation.get('relType'), relation.get('target')) for relation in synset.iter('SynsetRelation')])
     for synset in root.iter('Synset')},
    [(entry.find('Lemma').get('writtenForm'), entry.find('Lemma').get('partOfSpeech'),
      [(sense.get('id'), sense.get('synset')) for sense in entry.iter('Sense')])
     for entry in root.iter('LexicalEntry')])
del root

# Extra lists per category of the main meaning (nsgu-animal, nsgu-food, ...)
# and for vulgar words (nsgu-vulgar), also of the first parts with their
# linking element (bestimmungswort-animal, ...). They are sorted from the best
# known to the most obscure word, so the website can pick among the best known
# ones only. Words that may not be shown from a list come last, after the
# number of words in usable.txt: slurs, plurals and the like, and vulgar words
# except in the vulgar lists.
print("Finding categories and vulgar words ...")
info = WordInfo(entries, synsets, english, fugen)
del entries, synsets, english
extraWords = dict()
for word, pos in list(info.senses):
    if word in words.get(pos, ()):
        for extra in info.extra_lists(word, pos):
            keys = lists(word, pos) | ({'bestimmungswort'} if word in firstParts else set())
            for key in keys:
                extraWords.setdefault(key+'-'+extra, list())
                extraWords[key+'-'+extra].append((word, pos))
usable = dict()
for key, value in extraWords.items():
    extra = key.split('-', 1)[1]
    value.sort(key=lambda entry: info.rank(entry[0], entry[1], extra))
    usable[key] = sum(info.is_usable(word, pos, extra) for word, pos in value)
    extraWords[key] = [firstParts[word] if key.startswith('bestimmungswort-') else word for word, pos in value]
print("For example, the best known nouns per category:")
for key in sorted(extraWords):
    if key.startswith('nsgu-'):
        print("  "+key+": "+', '.join(extraWords[key][:12]))

# Slurs that two harmless words make up (Schlitz + Auge), as hashes so that
# the website can pick again instead of showing one.
hurtful = {word for word, pos in info.senses if info.is_hurtful(word, pos)} | HURTFUL_WORDS
harmless = [word for word in words['nsgu'] if not info.is_hurtful(word, 'n')]
blockedHashes = blocked(hurtful, {firstParts[word].lower() for word in harmless if word in firstParts},
                        {word.lower() for word in harmless})
print("Blocking "+str(len(blockedHashes))+" slurs made of two harmless words")

print("Generating files ...")
os.makedirs(startingDir, exist_ok=True)
with open(startingDir+'blocked.txt', 'w') as f:
    f.write('\n'.join(blockedHashes))
for key, value in words.items():
    writeList(key, value)
for key, value in extraWords.items():
    writeList(key, value, usable[key])

print("Finished!")
