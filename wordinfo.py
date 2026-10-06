"""What the generator knows about a word besides its spelling.

OdeNet, the German WordNet, has no word frequencies, but enough to tell the
funny words from the obscure ones:

- category:    the WordNet category most meanings of a word belong to (animal,
               food, person, artifact, ...), taken from the English WordNet
               OdeNet links its meanings to. Those links are often off (Hund
               has no meaning for the dog), so the compounds a word is the last
               part of vote as well: Schäferhund, Wachhund and Seehund make
               Hund an animal. Compounds without a category take the one of
               their last part (Hundekuchen like Kuchen).
- familiarity: how well known a word is. Common words show up in many compounds
               (Haus: Hausaufgabe, Rathaus, ...) and in the definitions of other
               words, have many meanings, and OdeNet marks about 1400 of them as
               basic vocabulary (Basiswortschatz). Obscure ones don't
               (Menorrhagie, Fruktifikation).
- vulgar:      crude, sexual and bathroom words and the compounds made of them
               (Arschgeige). They only show up in the vulgar lists, at the end of
               all others.
- hurtful:     slurs, words for groups of people by origin, religion, skin colour
               or sexual orientation (so that no name like Judenschwein comes up),
               words about abuse and the Nazis, and every compound with one of
               them. They never show up.
"""

import collections
import functools
import hashlib
import math
import re
from typing import NamedTuple

from fugen import MIN_SECOND_PART, NONE


def lists(word, pos):
    """The lists a word belongs to, named after its part of speech and spelling.

    For example nsgu: noun, single word (c for combined words), no dash (d for
    dash) and upper case letters (l for lower case only).
    """
    combined = 'c' if ' ' in word else 's'
    dash = 'd' if '-' in word else 'g'
    case = 'u' if any(char.isupper() for char in word) else 'l'
    return {pos, pos+combined, pos+dash, pos+case, pos+combined+dash, pos+combined+case, pos+combined+dash+case}


class Synset(NamedTuple):
    """A meaning of OdeNet, shared by all words that can express it."""
    ili: str          # link to the same meaning in the English WordNet, e.g. i35545
    subject: str      # OdeNet's category, e.g. noun.animal, often missing
    text: str         # definition and examples
    relations: list   # (relType, target synset)


class Entry(NamedTuple):
    """A word of OdeNet with its meanings."""
    word: str
    pos: str
    label: str        # usage label like ugs., derb or fachspr.
    basic: bool       # part of the basic vocabulary
    senses: list      # synset ids


class English(NamedTuple):
    """What the English WordNet knows about a meaning."""
    lexfile: str      # category, e.g. noun.animal
    slur: bool        # a slur against a group of people
    group: bool       # a group of people by origin, religion, skin colour, orientation or disability


# English words whose meanings for people, and everything below them (German,
# Turk, ...), are groups of people. Christians are left out, so that Christbaum
# and Christkind stay.
GROUPS = '''native national foreigner immigrant refugee Asian European African American Australian Jew Muslim
Hindu Buddhist Sikh person_of_color White_person Black_person Gypsy homosexual lesbian bisexual transgender
transsexual handicapped_person ethnic_group race'''.split()

SLUR_DEFINITION = re.compile(
    r'\b(ethnic slur|(offensive|derogatory|disparaging|contemptuous) (term|name|word) for)\b', re.I)


def english_meanings(synsets, entries):
    """Sums up the English WordNet per link (ILI).

    synsets: {id: (ili, lexfile, text, members, relations)}
    entries: [(word, pos, [(sense id, synset id)])]
    """
    sense_synset, meanings = {}, {}
    for word, pos, senses in entries:
        meanings[(word, pos)] = [synset for _, synset in senses]
        for sense, synset in senses:
            sense_synset[sense] = synset

    def label(target):
        """obscenity for the meaning 'obscenity', which other meanings exemplify"""
        synset = synsets.get(sense_synset.get(target, target))
        return synset[3][0].split('-', 1)[1].rsplit('-', 1)[0] if synset and synset[3] else ''

    roots = {synset for word in GROUPS for synset in meanings.get((word.replace('_', ' '), 'n'), ())
             if synsets[synset][1] in ('noun.person', 'noun.group')}
    children = collections.defaultdict(list)
    for synset_id, (ili, lexfile, text, members, relations) in synsets.items():
        for relation, target in relations:
            if relation in ('hypernym', 'instance_hypernym'):
                children[target].append(synset_id)
    groups, todo = set(roots), list(roots)
    while todo:
        for child in children[todo.pop()]:
            if child not in groups:
                groups.add(child)
                todo.append(child)

    english = {}
    for synset_id, (ili, lexfile, text, members, relations) in synsets.items():
        if ili and ili != 'in':
            labels = {label(target) for relation, target in relations if relation == 'exemplifies'}
            english[ili] = English(lexfile, 'ethnic_slur' in labels or bool(SLUR_DEFINITION.search(text)),
                                   synset_id in groups)
    return english


# Crude words, which also make every compound they are a part of crude
# (Arsch: Arschgeige, Affenarsch). In lower case.
VULGAR_WORDS = set('''arsch arschloch arschgeige arschkriecher arschbombe arschgeweih arschtritt hintern popo podex
allerwertester pöter pobacke hinterbacke anus scheiße scheiß schiss dünnschiss dünnpfiff kacke kacker pisse
pisser pipi furz pups schas kotze erbrochenes durchfall exkrement fäkalien urin rotz rotze popel schnodder
blähung flatulenz penis pimmel schniedel pillermann pillemann pullermann dödel gemächte klöten hoden vorhaut
erektion morgenlatte möse fotze votze vagina klitoris kitzler titte titten sperma ejakulat samenerguss orgasmus
fick bums wichser onanie masturbation sex oralsex gruppensex gangbang quickie koitus beischlaf fellatio
cunnilingus geilheit nymphomanin lustmolch lüstling porno pornografie pornographie striptease stripperin domina
dildo vibrator kondom präser präservativ verhüterli bordell puffmutter zuhälter nutte hure hurensohn hurenbock
dirne callgirl stricher strichmädchen kokotte schlampe flittchen luder bitch weibsstück miststück mistkerl
drecksack dreckskerl dreckschwein fettsack sauhund saubande sausack schweinehund schweinepriester zote fresse
hackfresse bastard bankert natursekt prostituierte prostituierter freudenhaus freudenmädchen driss shit shitstorm
bockmist mistding fäzes diarrhö diarrhöe diarrhoe hundstrümmerl harn piese urinal donnerbalken latrinenparole
notdurft speibsackerl flatus schoas leibwind pullerparty futt fott fudi fut vulva yoni phallus testikel skrotum
scrotum präputium lörres zumpferl sackhalter samenflüssigkeit lusttropfen godemiché coitus kopulation gevögel
selbstbefriedigung blasmaus blasehase fellatrix entjungferung voyeur exhibitionist perversion obszönität
schweinigelei sauerei erotik betthäschen wüstling tussi tusse prostitution kurtisane hetäre metze musche gigolo
callboy strichjunge lude loddel pimp kuppler strizzi tripper filzlaus hundesohn schweinebacke schweinebande
fettwanst dickwanst zimtzicke vollidiot knallidiot vollpfosten honk saustall'''.split())

# Crude words that are no crude part of a compound: Schwanz is crude, but
# Pferdeschwanz is a ponytail, and Kot is crude, but Kotflügel a fender.
VULGAR_ALONE = set('''schwanz muschi pussy busen brüste möpse hupen puff sau kot wichse'''.split())

# Slurs, words for groups of people OdeNet doesn't link to the English
# WordNet, and words about abuse and the Nazis. Every compound with one of them
# as a part is left out as well (Judenhass, Negerkuss). In lower case.
HURTFUL_WORDS = set('''kanake kanak polacke itaker itaka spaghettifresser kümmeltürke froschfresser kameltreiber
schlitzauge japse boche krauts tschingg tschusch piefke saupreiß russki iwan zoni ossi wessi bio-deutscher neger
nigger bimbo mohr zigeuner zigan rothaut squaw farbiger halbblut mischling hottentotte kaffer pygmäe
mohammedaner muselmann muselman muselmane jud jude itzig schickse mauschelei brunnenvergifter untermensch
volksgenosse fremdarbeiter gestapo gauleiter wehrmacht konzentrationslager vernichtungslager kapo holocaust
shoah schoah porajmos völkermord genozid massenmord endsieg machtergreifung hakenkreuz swastika
reichskristallnacht reichspogromnacht pogrom arier rassenhygiene rassenkunde rassenlehre rassentheorie euthanasie
blutschande braunhemd nazi neonazi hitler nationalsozialist nationalsozialismus faschist fascho asylant
scheinasylant asylschmarotzer sozialschmarotzer wirtschaftsflüchtling wohlstandsflüchtling penner
schwuler schwule schwulette schwuchtel schwuppe homo homosexueller homosexuelle homosexualität homoerotiker
homophiler homophilie homoehe schwulenehe homophobie lesbe lesbierin lesbentum kampflesbe tunte tucke transe
transi transvestit transsexualität transsexualismus transsexueller transsexuelle bisexualität heterosexualität
intersex intersexualität hermaphrodit zwitter hinterlader butch crossdresser spast spasti vollspast spacko
mongo mongolismus behinderter behinderte missgeburt liliputaner zwergmensch schwachsinniger debiler kretin
irrer geisteskranker geistesgestörter irrenanstalt irrenhaus klapse klapsmühle vergewaltigung vergewaltiger
notzucht missbrauch schändung kinderschänder knabenschänder päderast päderastie pädophiler pädophilie
pädosexueller inzest inzucht unzucht lolita nymphchen kindfrau zwangsprostitution menschenhandel
frauenhandel zwangsheirat genitalverstümmelung frauenbeschneidung misshandlung kindsmord kindstötung reisfresser
mandelauge mof tschingili franzacke franzmann schangel tatern musel jidd fremdstämmiger türkendeutsch
armutsflüchtling schrumpfgermane goebbels göring himmler eichmann faschismus skinhead tötungsfabrik todeslager
mordfabrik massenvernichtung exterminierung arisierer ariseur eugenik eugenetik kaukasoid rassentrennung
apartheid lynchjustiz blutgerücht blutbeschuldigung blutanklage sigrune siegrune gleichschaltung infibulation
infantizid kindestötung assi asis asozialer asoziale ss sa kz kl'''.split()) | {
    'drittes reich', 'tausendjährige reich', 'deutscher gruß', 'geheime staatspolizei', 'schwarze schande',
    'schwarzer sklave', 'nürnberger gesetze', 'eingetragene partnerschaft', 'mensch mit behinderung',
    'person mit behinderung', 'warmer bruder', 'kesser vater', 'drag queen', 'kanak sprak'}

# Words that look crude to the rules above but aren't: das Mensch is an old
# crude word for a woman, but der Mensch is not.
NOT_VULGAR = set('''mensch viecher dingsbums pipifax multivibrator'''.split())

# OdeNet's labels for technical, elevated or old-fashioned words, which only come with ?nerd
NERDY_LABEL = re.compile(r'fachspr|geh\.|gehoben|bildungssprachlich|veraltet|wissenschaftlich|jargon|lat\.|selten',
                         re.I)
VULGAR_LABEL = re.compile(r'derb|vulg|obszön', re.I)


class WordInfo:
    """Category, familiarity and vulgarity of every word of the dictionary."""

    def __init__(self, entries, synsets, english, fugen):
        self.synsets = synsets
        self.english = english
        self.fugen = fugen
        self.senses = {}   # (word, pos) -> synsets
        self.labels = collections.defaultdict(str)
        self.basic = set()
        for entry in entries:
            key = (entry.word, entry.pos)
            self.senses.setdefault(key, []).extend(synset for synset in entry.senses if synset in synsets)
            if entry.label:
                self.labels[key] += entry.label + ', '
            if entry.basic:
                self.basic.add(key)
        self.adjectives = {word.lower() for word, pos in self.senses if pos == 'a'}

        # Familiarity signals
        self.in_texts = collections.Counter(
            token for synset in synsets.values() for token in re.findall(r'\w+', synset.text.lower()))
        self.meanings = collections.Counter()
        for (word, pos), meanings in self.senses.items():
            self.meanings[word] += len(meanings)
        # how often a noun is the first part of a compound, and which compounds it is the last part of
        self.lexicon = {word.lower() for word, pos in self.senses if pos == 'n' and word.isalpha() and len(word) >= 3}
        self.as_first = collections.Counter({noun: sum(counter.values()) for noun, counter in fugen.counts.items()})
        self.heads = {}   # compound -> its longest last part, all in lower case
        self.compounds = collections.defaultdict(list)   # last part -> compounds
        for compound in self.lexicon:
            for split in range(3, len(compound) - MIN_SECOND_PART + 1):
                if compound[split:] in self.lexicon and compound[:split] in fugen.starts:
                    self.heads.setdefault(compound, compound[split:])
                    self.compounds[compound[split:]].append(compound)
        self.nouns = {word.lower(): word for word, pos in self.senses if pos == 'n'}

    def english_of(self, synset_id):
        return self.english.get(self.synsets[synset_id].ili)

    def categories(self, word, pos):
        """The categories of the meanings of a word, as far as known."""
        found = collections.Counter()
        for synset in self.senses.get((word, pos), ()):
            english = self.english_of(synset)
            lexfile = english.lexfile if english else self.synsets[synset].subject
            if lexfile:
                found[lexfile.split('.')[1].lower()] += 1
        return found

    @functools.lru_cache(maxsize=None)
    def category(self, word, pos):
        """The category most meanings of the word and of the compounds ending with it
        belong to: animal, food, person, all (adjectives), ..."""
        votes = self.categories(word, pos)
        if pos == 'n':
            for compound in self.compounds.get(word.lower(), ()):
                own = self.categories(self.nouns[compound], 'n')
                if own:
                    votes[own.most_common(1)[0][0]] += 1
            if not votes:
                head = self.heads.get(word.lower())
                if head:
                    return self.category(self.nouns[head], 'n')
        return votes.most_common(1)[0][0] if votes else 'other'

    @functools.lru_cache(maxsize=None)
    def familiarity(self, word, pos):
        """A score for how well known a word is: about 0 for Menorrhagie, 20 for Haus."""
        lower = word.lower()
        in_texts = sum(self.in_texts[lower + ending] for ending in ('', 'e', 'n', 'en', 'er', 'es', 's'))
        as_last = len(self.compounds.get(lower, ()))
        return (math.log2(1 + in_texts) + math.log2(1 + self.as_first[lower]) + math.log2(1 + as_last)
                + 1.5 * math.log2(max(1, self.meanings[word])) + 3 * ((word, pos) in self.basic))

    @functools.lru_cache(maxsize=None)
    def parts(self, word):
        """The word in lower case and all nouns it is made of: Arschgeige -> arschgeige, arsch, geige."""
        found = {word.lower()}
        for token in re.split('[ -]+', word.lower()):
            found |= self.compound_parts(token)
        return frozenset(found)

    @functools.lru_cache(maxsize=None)
    def compound_parts(self, lower):
        found = {lower}
        for split in range(3, len(lower) - 2):
            head = lower[split:]
            if head in self.lexicon:
                for noun, fuge in self.fugen.starts.get(lower[:split], ()):
                    # only the linking element the noun usually takes (Sauerstoff is no Sau + er + Stoff),
                    # and no abbreviations (Abmarsch is no ABM + Arsch)
                    if fuge == self.fugen.attested.get(noun, NONE) and self.nouns.get(noun, '')[1:].islower():
                        found |= self.compound_parts(noun) | self.compound_parts(head)
        return found

    @functools.lru_cache(maxsize=None)
    def is_group(self, word, pos):
        """Whether any meaning of the word is a slur or a group of people by origin, religion, ..."""
        return any(getattr(self.english_of(synset), 'slur', False) or getattr(self.english_of(synset), 'group', False)
                   for synset in self.senses.get((word, pos), ()))

    @functools.lru_cache(maxsize=None)
    def is_hurtful(self, word, pos):
        return self.is_group(word, pos) or any(
            part in HURTFUL_WORDS or part in self.nouns and self.is_group(self.nouns[part], 'n')
            for part in self.parts(word))

    def is_crude(self, word, pos):
        """Whether the word is or contains one of the hand-picked crude words."""
        return word.lower() in VULGAR_ALONE or bool(self.parts(word) & VULGAR_WORDS)

    @functools.lru_cache(maxsize=None)
    def is_vulgar(self, word, pos):
        if self.is_hurtful(word, pos) or word.lower() in NOT_VULGAR:
            return False
        return self.is_crude(word, pos) or bool(VULGAR_LABEL.search(self.labels[(word, pos)]))

    @functools.lru_cache(maxsize=None)
    def is_plural(self, word, pos):
        """Plurals like Maschinen, Regeln, Erwartungen or Lehrerinnen, which make dull names.

        A plural is less known than its singular, which tells Maschinen from
        Essen (not the plural of Esse) and Laden (not the plural of Lade)."""
        lower = word.lower()
        if pos != 'n':
            return False
        singulars = []
        if lower.endswith('n') and re.search('(e|el|er)$', lower[:-1]):
            singulars.append(lower[:-1])
        if lower.endswith('en') and re.search('(ung|heit|keit|schaft|ion|tät|ik|ist|ent|ant)$', lower[:-2]):
            singulars.append(lower[:-2])
        if lower.endswith('innen'):
            singulars.append(lower[:-3])
        return any(singular in self.nouns and self.familiarity(self.nouns[singular], 'n') > self.familiarity(word, pos)
                   for singular in singulars)

    def is_nerdy(self, word, pos):
        """Technical and old words, abbreviations and adjectives used as nouns (Alte, Grüne)."""
        return bool(NERDY_LABEL.search(self.labels[(word, pos)]) or not word.replace(' ', '').isalpha()
                    or not word[1:].replace(' ', '').islower()
                    or pos == 'n' and re.sub('(e|er|es|en)$', '', word.lower()) in self.adjectives)

    def is_usable(self, word, pos, extra=None):
        """Whether the word may be shown from an extra list: never slurs or plurals,
        and vulgar words only from the vulgar lists."""
        return (not self.is_hurtful(word, pos) and not self.is_plural(word, pos)
                and self.is_vulgar(word, pos) == (extra == 'vulgar'))

    def rank(self, word, pos, extra=None):
        """Sort key for an extra list: familiar words first, words that may not be shown from it last.

        The vulgar lists start with the hand-picked crude words, the others
        put technical words after all well-known ones."""
        first = self.is_crude(word, pos) if extra == 'vulgar' else not self.is_nerdy(word, pos)
        return (not self.is_usable(word, pos, extra), not first, -self.familiarity(word, pos), word)

    def extra_lists(self, word, pos):
        """The extra lists a word belongs to: its category, and vulgar."""
        extras = [self.category(word, pos)]
        if self.is_vulgar(word, pos):
            extras.append('vulgar')
        return extras


def blocked_hash(name):
    """A short hash of a name in lower case without spaces and dashes, see blocked()."""
    return hashlib.sha256(re.sub('[ -]', '', name.lower()).encode('utf-8')).hexdigest()[:16]


def blocked(hurtful, firsts, seconds):
    """Hashes of the hurtful words that two harmless words can make up (Schlitz + Auge),
    so that the website can pick again when it comes up with one of them."""
    hashes = set()
    for word in hurtful:
        lower = re.sub('[ -]', '', word.lower())
        if any(lower[:split] in firsts and lower[split:] in seconds for split in range(1, len(lower))):
            hashes.add(blocked_hash(lower))
    return sorted(hashes)
