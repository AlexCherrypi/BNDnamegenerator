from defusedxml.minidom import parseString
import gzip 
import requests
from random import randint
import os

startingDir = './website/words/'


url = 'https://github.com/hdaSprachtechnologie/odenet/blob/master/odenet/wordnet/deWordNet.xml'
print("Downloading from '"+ url +"'")
download = requests.get(url).content
print("Download from '"+ url +"' finished")
del url
# print("Decopressing ...")
#xml = gzip.decompress(download).decode("utf-8")
xml = download
del download
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
    if not word.isdigit() and len(word) > 2:
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
            words.setdefault(pos+'g',set()) # l for lower 
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

print("Generating files ...")
for  key, value in words.items():
    os.makedirs(startingDir+key, exist_ok=True)
    print("Generating files for key '"+key+"' in '"+os.path.abspath(startingDir+key)+"'...")
    pos = 0
    for word in words[key]:
        with open(startingDir+key+'/'+str(pos)+'.txt', 'w') as f:
            f.write(word)
        pos = pos + 1
    with open(startingDir+key+'/len.txt', 'w') as f:
            f.write(str(pos))

print("Finished!")

