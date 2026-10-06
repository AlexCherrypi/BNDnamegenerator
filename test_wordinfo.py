import unittest

from fugen import Fugen
from wordinfo import English, Entry, Synset, WordInfo, blocked, blocked_hash, lists


def wordnet():
    """A tiny dictionary in the shape generateWords.py reads from OdeNet."""
    english = {
        'i-animal': English('noun.animal', False, False),
        'i-firedog': English('noun.artifact', False, False),
        'i-food': English('noun.food', False, False),
        'i-artifact': English('noun.artifact', False, False),
        'i-jew': English('noun.person', False, True),
        'i-body': English('noun.body', False, False),
    }
    synsets = {
        'hund-1': Synset('i-firedog', None, 'Metallstützen für Holzscheite', []),
        'schäferhund': Synset('i-animal', None, 'ein Hund, der Schafe hütet', []),
        'wachhund': Synset('i-animal', None, 'ein Hund, der wacht', []),
        'katze': Synset('i-animal', None, 'ein Tier, das jagt; die Katze jagt den Hund nicht', []),
        'kuchen': Synset('i-food', None, 'ein Gebäck', []),
        'hundekuchen': Synset(None, None, 'Kuchen für Hunde', []),
        'hütte': Synset('i-artifact', None, 'ein kleines Haus', []),
        'maschine': Synset('i-artifact', None, 'eine Maschine, die arbeitet', []),
        'maschinen': Synset('i-artifact', None, 'Maschinen in ihrer Gesamtheit', []),
        'esse': Synset('i-artifact', None, 'ein Schornstein', []),
        'essen': Synset('i-food', None, 'Essen und Trinken, das Essen', []),
        'jude': Synset('i-jew', None, 'ein Angehöriger des Judentums', []),
        'stern': Synset('i-artifact', None, 'ein Himmelskörper', []),
        'judenstern': Synset('i-artifact', None, 'ein Abzeichen', []),
        'arsch': Synset('i-body', None, 'das Gesäß', []),
        'geige': Synset('i-artifact', None, 'ein Instrument', []),
        'arschgeige': Synset(None, None, 'ein dummer Mensch', []),
        'schwanz': Synset('i-body', None, 'der Schwanz eines Tieres', []),
        'pferd': Synset('i-animal', None, 'ein Tier zum Reiten', []),
        'pferdeschwanz': Synset('i-body', None, 'eine Frisur', []),
        'sau': Synset('i-animal', None, 'ein weibliches Schwein', []),
        'stoff': Synset('i-artifact', None, 'ein Material', []),
        'sauerstoff': Synset(None, 'noun.substance', 'ein Gas', []),
        'mensch': Synset('i-animal', None, 'ein Lebewesen', []),
        'klepper': Synset('i-animal', None, 'ein altes Pferd', []),
        'menorrhagie': Synset(None, 'noun.state', 'eine Blutung', []),
        'fut': Synset('i-body', None, 'die Vulva', []),
        'futter': Synset('i-food', None, 'Nahrung für Tiere', []),
    }
    entries = [Entry(word, 'n', label, basic, senses) for word, label, basic, senses in [
        ('Hund', '', True, ['hund-1']), ('Schäfer', '', False, []), ('Wache', '', False, []),
        ('Schäferhund', '', False, ['schäferhund']),
        ('Wachhund', '', False, ['wachhund']), ('Katze', '', True, ['katze']), ('Kuchen', '', True, ['kuchen']),
        ('Hundekuchen', '', False, ['hundekuchen']), ('Hütte', '', False, ['hütte']),
        ('Hundehütte', '', False, ['hütte']), ('Maschine', '', True, ['maschine']),
        ('Maschinen', '', False, ['maschinen']), ('Esse', '', False, ['esse']), ('Essen', '', True, ['essen']),
        ('Jude', '', False, ['jude']), ('Stern', '', True, ['stern']), ('Judenstern', '', False, ['judenstern']),
        ('Arsch', 'derb', False, ['arsch']), ('Geige', '', False, ['geige']),
        ('Arschgeige', 'derb', False, ['arschgeige']), ('Schwanz', '', False, ['schwanz']),
        ('Pferd', '', True, ['pferd']), ('Pferdeschwanz', '', False, ['pferdeschwanz']),
        ('Sau', '', False, ['sau']), ('Stoff', '', True, ['stoff']), ('Sauerstoff', '', False, ['sauerstoff']),
        ('Mensch', 'derb', True, ['mensch']), ('Klepper', 'derb, abwertend', False, ['klepper']),
        ('Menorrhagie', 'fachspr.', False, ['menorrhagie']), ('Fut', '', False, ['fut']),
        ('Futter', '', True, ['futter']),
    ]]
    fugen = Fugen([entry.word for entry in entries])
    return WordInfo(entries, synsets, english, fugen)


class ListsTest(unittest.TestCase):

    def test_lists(self):
        self.assertEqual(lists('Hund', 'n'), {'n', 'ns', 'ng', 'nu', 'nsg', 'nsu', 'nsgu'})
        self.assertEqual(lists('alter Sack', 'n'), {'n', 'nc', 'ng', 'nu', 'ncg', 'ncu', 'ncgu'})


class WordInfoTest(unittest.TestCase):

    def setUp(self):
        self.info = wordnet()

    def test_compounds_vote_for_the_category(self):
        # Hund's only meaning is linked to a fire dog, but Schäferhund and Wachhund are animals
        self.assertEqual(self.info.category('Hund', 'n'), 'animal')
        self.assertEqual(self.info.category('Katze', 'n'), 'animal')

    def test_compound_takes_the_category_of_its_last_part(self):
        self.assertEqual(self.info.category('Hundekuchen', 'n'), 'food')
        self.assertEqual(self.info.category('Sauerstoff', 'n'), 'substance')

    def test_familiarity(self):
        self.assertGreater(self.info.familiarity('Hund', 'n'), self.info.familiarity('Menorrhagie', 'n'))

    def test_parts(self):
        self.assertEqual(self.info.parts('Hundekuchen'), {'hundekuchen', 'hund', 'kuchen'})
        self.assertEqual(self.info.parts('Arschgeige'), {'arschgeige', 'arsch', 'geige'})
        # Sau links without an er, so Sauerstoff is no Sau
        self.assertNotIn('sau', self.info.parts('Sauerstoff'))

    def test_hurtful(self):
        self.assertTrue(self.info.is_hurtful('Jude', 'n'))         # a group of people
        self.assertTrue(self.info.is_hurtful('Judenstern', 'n'))   # a compound with one
        self.assertFalse(self.info.is_hurtful('Stern', 'n'))
        self.assertFalse(self.info.is_usable('Jude', 'n', 'person'))

    def test_vulgar(self):
        self.assertTrue(self.info.is_vulgar('Arsch', 'n'))
        self.assertTrue(self.info.is_vulgar('Arschgeige', 'n'))      # a crude part
        self.assertTrue(self.info.is_vulgar('Schwanz', 'n'))
        self.assertFalse(self.info.is_vulgar('Pferdeschwanz', 'n'))  # a ponytail
        self.assertFalse(self.info.is_vulgar('Sauerstoff', 'n'))
        self.assertTrue(self.info.is_vulgar('Fut', 'n'))
        self.assertFalse(self.info.is_vulgar('Futter', 'n'))         # crude only on its own
        self.assertTrue(self.info.is_vulgar('Klepper', 'n'))         # labelled derb
        self.assertFalse(self.info.is_vulgar('Mensch', 'n'))         # only das Mensch is crude
        self.assertFalse(self.info.is_usable('Arsch', 'n', 'body'))
        self.assertTrue(self.info.is_usable('Arsch', 'n', 'vulgar'))

    def test_plural(self):
        self.assertTrue(self.info.is_plural('Maschinen', 'n'))
        self.assertFalse(self.info.is_plural('Maschine', 'n'))
        self.assertFalse(self.info.is_plural('Essen', 'n'))   # better known than Esse, so no plural of it

    def test_nerdy_words_come_after_known_ones(self):
        self.assertTrue(self.info.is_nerdy('Menorrhagie', 'n'))
        self.assertFalse(self.info.is_nerdy('Hund', 'n'))
        ranked = sorted(['Menorrhagie', 'Sauerstoff'], key=lambda word: self.info.rank(word, 'n', 'state'))
        self.assertEqual(ranked[0], 'Sauerstoff')

    def test_crude_words_first_in_vulgar_lists(self):
        ranked = sorted(['Klepper', 'Arschgeige'], key=lambda word: self.info.rank(word, 'n', 'vulgar'))
        self.assertEqual(ranked, ['Arschgeige', 'Klepper'])

    def test_extra_lists(self):
        self.assertEqual(self.info.extra_lists('Katze', 'n'), ['animal'])
        self.assertEqual(self.info.extra_lists('Arsch', 'n'), ['body', 'vulgar'])


class BlockedTest(unittest.TestCase):

    def test_slurs_made_of_two_harmless_words(self):
        hashes = blocked({'Schlitzauge', 'Kanake'}, {'schlitz', 'kanak'}, {'auge'})
        self.assertEqual(hashes, [blocked_hash('schlitzauge')])
        self.assertEqual(blocked_hash('SCHLITZ-AUGE'), blocked_hash('schlitzauge'))


if __name__ == '__main__':
    unittest.main()
