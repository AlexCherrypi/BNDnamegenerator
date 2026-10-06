from defusedxml.minidom import parseString
import requests
import random
import os
from fugen import Fugen

startingDir = './website/words/'


url = 'https://raw.githubusercontent.com/hdaSprachtechnologie/odenet/master/odenet/wordnet/deWordNet.xml'
print("Downloading from '"+ url +"'")
response = requests.get(url, timeout=600)
response.raise_for_status()
xml = response.content
del response
print("Download from '"+ url +"' finished")
del url
print("Parsing xml ...")
file = parseString(xml)
del xml
print("Finding Lemmas ...")
lemmas = file.getElementsByTagName('Lemma')
del file
words = dict()

print("Finding and sorting words ...")
for lemma in lemmas:
    pos  = lemma.getAttribute('partOfSpeech')
    word = lemma.getAttribute('writtenForm')
    if not word.isdigit() and not any(e in word for e in ['.',',','/','\\',')','(']) and len(word) > 2:
        words.setdefault(pos,set())
        words[pos].add(word)
        name = pos
        name2 = pos
        if ' ' in word:
            name = name +'c'
            name2 = name2 +'c'
            words.setdefault(pos+'c',set()) # c for combined 
            words[pos+'c'].add(word)
        else: 
            name = name +'s'
            name2 = name2 +'s'
            words.setdefault(pos+'s',set()) # s for single 
            words[pos+'s'].add(word)

        if '-' in word:
            name = name +'d'
            words.setdefault(pos+'d',set()) # d for dash
            words[pos+'d'].add(word)
        else: 
            name = name +'g'
            words.setdefault(pos+'g',set()) # g for no dash 
            words[pos+'g'].add(word)

        words.setdefault(name,set()) # combined
        words[name].add(word)

        if any(char.isupper() for char in word):
            name = name +'u'
            name2 = name2 +'u'
            words.setdefault(pos+'u',set()) # u for upper 
            words[pos+'u'].add(word)
        else: 
            name = name +'l'
            name2 = name2 +'l'
            words.setdefault(pos+'l',set()) # l for lower 
            words[pos+'l'].add(word)

        words.setdefault(name,set()) # combined
        words[name].add(word)
        words.setdefault(name2,set()) # combined
        words[name2].add(word)
del lemmas

# The first word of a name gets its linking element already attached
# (Sonne -> Sonnen, Zeitung -> Zeitungs), see fugen.py
print("Choosing linking elements ...")
fugen = Fugen(words['nsgu'])
words['bestimmungswort'] = set()
reasons = dict()
for noun in words['nsgu']:
    decision = fugen.decide(noun)
    reason = decision[1] if decision else 'left out'
    reasons[reason] = reasons.get(reason, 0) + 1
    if decision:
        words['bestimmungswort'].add(decision[0].apply(noun))
print("Linking elements by "+ str(reasons) +", for example:")
for noun in random.sample(sorted(words['nsgu']), 20):
    print("  "+ fugen.explain(noun))

print("Generating files ...")
for  key, value in words.items():
    os.makedirs(startingDir+key, exist_ok=True)
    print("Generating files for key '"+key+"' in '"+os.path.abspath(startingDir+key)+"'...")
    pos = 0
    for word in words[key]:
        with open(startingDir+key+'/'+str(pos)+'.txt', 'w', encoding="utf-8") as f:
            f.write(word)
        pos = pos + 1
    with open(startingDir+key+'/len.txt', 'w') as f:
            f.write(str(pos))

print("Finished!")

