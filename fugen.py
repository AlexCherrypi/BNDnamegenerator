"""Linking elements (Fugenelemente) for German noun compounds.

When German glues two nouns together, the first one often changes its ending:

    Haus    + Tür    -> Haustür          (nothing)
    Zeitung + Papier -> Zeitungspapier   (+s)
    Sonne   + Blume  -> Sonnenblume      (+n)
    Kind    + Garten -> Kindergarten     (+er)
    Schule  + Bus    -> Schulbus         (-e)
    Hilfe   + Mittel -> Hilfsmittel      (-e +s)
    Buch    + Regal  -> Bücherregal      (umlaut +er)

Which linking element a noun takes is largely a matter of vocabulary, so no set
of rules gets every word right. This module therefore decides in four steps,
from most to least reliable:

1. attested: The dictionary contains compounds that start with the word
             (Sonnenblume, Sonnenschein, Sonnenbrille, ...), so do the same.
2. rule:     A few rules of German grammar that hold almost without exception,
             e.g. words on -ung, -heit or -keit always take an s.
3. analogy:  Words with the same ending usually behave the same. Zustand,
             Vorstand and Bestand take an s, so Wohlstand gets one as well.
4. fallback: Without any hint, the words are simply joined, which is what
             most nouns do. Words ending in -e are left out instead, because
             they go every which way (Sonnen-, Schul-, Hilfs-, Kaffee-).

Abbreviations like NATO or LKW are always joined as they are.
"""

import collections
import re
from typing import NamedTuple


class Fuge(NamedTuple):
    """How a noun changes when it becomes the first part of a compound."""

    strip: str = ''        # ending removed first: Schule -> Schul
    umlaut: bool = False   # last vowel gets an umlaut: Buch -> Büch
    add: str = ''          # linking element appended: Zeitung -> Zeitungs

    def apply(self, word):
        """Return the word as first part of a compound, or None if this doesn't fit the word."""
        if self.strip:
            if not word.endswith(self.strip) or len(word) < len(self.strip) + 2:
                return None
            word = word[:-len(self.strip)]
        if self.umlaut:
            word = umlaut(word)
            if word is None:
                return None
        return word + self.add

    @property
    def changes_stem(self):
        return bool(self.strip) or self.umlaut

    def __str__(self):
        parts = ['-' + self.strip] if self.strip else []
        if self.umlaut:
            parts.append('umlaut')
        if self.add:
            parts.append('+' + self.add)
        return ' '.join(parts) or 'no linking element'


NONE = Fuge()

# Linking elements that rules and analogies may assign to any word.
COMMON_FUGEN = (
    NONE,                           # Haustür
    Fuge(add='s'),                  # Zeitungspapier
    Fuge(add='n'),                  # Sonnenblume
    Fuge(add='en'),                 # Menschenmenge
    Fuge(add='e'),                  # Hundehütte
    Fuge(add='er'),                 # Kindergarten
    Fuge(strip='e'),                # Schulbus
    Fuge(strip='e', add='s'),       # Hilfsmittel
)

# Linking elements that belong to a few particular words only. They are used
# for words seen with them in at least two compounds of the dictionary.
SPECIAL_FUGEN = (
    Fuge(add='es'),                 # Tageslicht
    Fuge(add='ens'),                # Herzensbrecher
    Fuge(strip='in', add='innen'),  # Lehrerinnenzimmer
    Fuge(umlaut=True, add='e'),     # Gästezimmer
    Fuge(umlaut=True, add='er'),    # Bücherregal
    Fuge(strip='a', add='en'),      # Firmenwagen
    Fuge(strip='um', add='en'),     # Datenbank
    Fuge(strip='us', add='en'),     # Virenscanner
)

ALL_FUGEN = COMMON_FUGEN + SPECIAL_FUGEN

# Rules of German grammar: (word ending, linking element, examples).
# A rule only applies if a vowel comes before the ending, so that Sprung is not
# taken for an -ung word.
RULES = (
    # these suffixes always take an s
    (r'(ung|heit|keit|schaft|ion|tät|ling|tum)$', Fuge(add='s'),
     'Zeitungspapier, Freiheitskampf, Gesellschaftsspiel, Informationsquelle, '
     'Universitätsklinik, Frühlingsanfang, Eigentumswohnung'),
    # people on -ist (but not Frist or Mist)
    (r'(?<=[aeiouäöü][^aeiouäöü])ist$', Fuge(add='en'),
     'Touristenfalle, Polizistenmütze, Juristendeutsch'),
    # women on -in
    (r'(er|ist|ent|ant)in$', Fuge(strip='in', add='innen'),
     'Lehrerinnenzimmer, Studentinnenwohnheim'),
    (r'(chen|lein|er|el)$', NONE,
     'Mädchenname, Fräuleinwunder, Lehrerzimmer, Apfelbaum'),
    (r'(ik|ur|enz|nis|eur|iv|ismus|ee)$', NONE,
     'Musikschule, Kulturbeutel, Lizenzgebühr, Ergebnisliste, Ingenieurbüro, '
     'Archivbild, Tourismusbranche, Kaffeetasse'),
    # after a hissing sound there is no room for another s
    (r'(s|ß|x|z|sch)$', NONE,
     'Busfahrer, Fußball, Boxkampf, Salzstreuer, Tischbein'),
)

# A compound must leave at least this many letters for its second part, so
# that short leftovers like "Ei" or "Ar" do not count as compounds.
MIN_SECOND_PART = 4

# Verb particles look like the start of a compound (Ausgang, Entwicklung) but
# are not nouns, so they must not be mistaken for Aue + s or Ente - e.
PARTICLES = frozenset((
    'auf', 'aus', 'bei', 'durch', 'ein', 'ent', 'fort', 'hinter', 'miss',
    'mit', 'nach', 'rück', 'über', 'unter', 'ver', 'vor', 'wider', 'zer', 'zurück',
))

# An analogy needs an ending of at least MIN_ENDING letters shared by at least
# MIN_SUPPORT attested words, of which at least MIN_SHARE agree.
MIN_ENDING = 3
MIN_SUPPORT = 3
MIN_SHARE = 0.8

UMLAUTS = {'a': 'ä', 'o': 'ö', 'u': 'ü', 'au': 'äu', 'aa': 'ä', 'oo': 'ö',
           'A': 'Ä', 'O': 'Ö', 'U': 'Ü', 'Au': 'Äu'}


def umlaut(word):
    """Put an umlaut on the last vowel: Buch -> Büch, Haus -> Häus, Arzt -> Ärzt."""
    vowels = list(re.finditer('[aeiouäöüAEIOUÄÖÜ]+', word))
    if not vowels or vowels[-1].group() not in UMLAUTS:
        return None
    last = vowels[-1]
    return word[:last.start()] + UMLAUTS[last.group()] + word[last.end():]


def by_rule(word):
    """Return (linking element, examples) of the first matching rule, or None."""
    lower = word.lower()
    for ending, fuge, examples in RULES:
        match = re.search(ending, lower)
        if match and re.search('[aeiouäöüy]', lower[:match.start()]):
            return fuge, examples
    return None


def attested_fugen(nouns):
    """Count which linking element each noun uses in compounds of the dictionary.

    Returns {noun in lower case: Counter({linking element: number of compounds})}.
    """
    lexicon = {noun.lower() for noun in nouns if noun.isalpha() and len(noun) >= 3}

    # all ways a compound can start, e.g. 'sonnen' -> [('sonne', +n)]
    starts = collections.defaultdict(list)
    for noun in lexicon:
        for fuge in ALL_FUGEN:
            start = fuge.apply(noun)
            if start and len(start) >= 3 and start not in PARTICLES:
                starts[start].append((noun, fuge))

    counts = collections.defaultdict(collections.Counter)
    for compound in lexicon:
        for split in range(3, len(compound) - MIN_SECOND_PART + 1):
            if compound[split:] not in lexicon:
                continue
            candidates = starts.get(compound[:split], [])
            # Hausmittel is Haus + Mittel rather than Haue - e + s + Mittel:
            # if the start works without changing a noun's stem, prefer that.
            if any(not fuge.changes_stem for _, fuge in candidates):
                candidates = [(noun, fuge) for noun, fuge in candidates if not fuge.changes_stem]
            for noun, fuge in candidates:
                counts[noun][fuge] += 1
    return counts


def most_common_fuge(counter):
    """Pick the linking element a noun uses most, preferring simpler ones on a tie."""
    usable = [(fuge, count) for fuge, count in counter.items()
              if fuge in COMMON_FUGEN or count >= 2]
    if not usable:
        return None
    return max(usable, key=lambda item: (item[1], -ALL_FUGEN.index(item[0])))[0]


class Fugen:
    """Decides the linking element of nouns, learning from the given dictionary."""

    def __init__(self, nouns):
        self.counts = attested_fugen(nouns)
        self.attested = {}
        for noun, counter in self.counts.items():
            fuge = most_common_fuge(counter)
            if fuge is not None:
                self.attested[noun] = fuge
        # how often each word ending goes with which linking element
        self.endings = collections.defaultdict(collections.Counter)
        for noun, fuge in self.attested.items():
            if fuge in COMMON_FUGEN:
                for length in range(MIN_ENDING, len(noun) + 1):
                    self.endings[noun[-length:]][fuge] += 1

    def by_analogy(self, word):
        """Return (linking element, ending) learned from words with the same ending, or None."""
        lower = word.lower()
        # the longest ending known well enough decides
        for length in range(len(lower) - 1, MIN_ENDING - 1, -1):
            counter = self.endings.get(lower[-length:])
            if counter is None or sum(counter.values()) < MIN_SUPPORT:
                continue
            fuge, count = counter.most_common(1)[0]
            if count / sum(counter.values()) >= MIN_SHARE and fuge.apply(word):
                return fuge, lower[-length:]
            return None
        return None

    def decide(self, word):
        """Return (linking element, reason), or None if the word is too uncertain to use."""
        lower = word.lower()
        if lower in self.attested and self.attested[lower].apply(word):
            return self.attested[lower], 'attested'
        if not word.isalpha() or word.isupper():
            return NONE, 'abbreviation'
        rule = by_rule(word)
        if rule:
            return rule[0], 'rule'
        analogy = self.by_analogy(word)
        if analogy:
            return analogy[0], 'analogy'
        if lower.endswith('e'):
            return None
        return NONE, 'fallback'

    def first_part(self, word):
        """Return the word as first part of a compound (Sonne -> Sonnen), or None."""
        decision = self.decide(word)
        return decision[0].apply(word) if decision else None

    def explain(self, word):
        """Describe in one line how the word is used as first part of a compound."""
        decision = self.decide(word)
        if decision is None:
            return word + ': left out, linking element unclear'
        fuge, reason = decision
        text = word + ' -> ' + fuge.apply(word) + ' (' + str(fuge) + ', ' + reason
        if reason == 'attested':
            count = self.counts[word.lower()][fuge]
            text += ' in ' + str(count) + (' compound' if count == 1 else ' compounds')
        elif reason == 'rule':
            text += ' like ' + by_rule(word)[1]
        elif reason == 'analogy':
            ending = self.by_analogy(word)[1]
            text += ' to words ending in -' + ending + ': ' + ', '.join(
                str(f) + ' ' + str(n) + 'x' for f, n in self.endings[ending].most_common(3))
        return text + ')'
