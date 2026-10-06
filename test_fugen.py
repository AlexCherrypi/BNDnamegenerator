import unittest

from fugen import Fuge, Fugen, NONE, by_rule


class FugeTest(unittest.TestCase):

    def test_apply(self):
        self.assertEqual(NONE.apply('Haus'), 'Haus')
        self.assertEqual(Fuge(add='s').apply('Zeitung'), 'Zeitungs')
        self.assertEqual(Fuge(strip='e').apply('Schule'), 'Schul')
        self.assertEqual(Fuge(strip='e', add='s').apply('Hilfe'), 'Hilfs')
        self.assertEqual(Fuge(strip='a', add='en').apply('Firma'), 'Firmen')
        self.assertEqual(Fuge(strip='in', add='innen').apply('Lehrerin'), 'Lehrerinnen')

    def test_apply_umlaut(self):
        self.assertEqual(Fuge(umlaut=True, add='er').apply('Buch'), 'Bücher')
        self.assertEqual(Fuge(umlaut=True, add='er').apply('Haus'), 'Häuser')
        self.assertEqual(Fuge(umlaut=True, add='e').apply('Arzt'), 'Ärzte')

    def test_apply_does_not_fit(self):
        self.assertIsNone(Fuge(strip='e').apply('Haus'))
        self.assertIsNone(Fuge(strip='e').apply('Ee'))
        self.assertIsNone(Fuge(umlaut=True, add='er').apply('Tisch'))

    def test_apply_follows_german_sounds(self):
        self.assertEqual(Fuge(add='n').apply('Bauer'), 'Bauern')
        self.assertEqual(Fuge(strip='um', add='en').apply('Medium'), 'Medien')
        self.assertIsNone(Fuge(add='n').apply('Wulst'))
        self.assertIsNone(Fuge(add='s').apply('Mus'))
        self.assertIsNone(Fuge(strip='e').apply('Magie'))


class RuleTest(unittest.TestCase):

    def assertRule(self, word, fuge):
        rule = by_rule(word)
        self.assertIsNotNone(rule, word)
        self.assertEqual(rule[0], fuge, word)

    def test_rules(self):
        for word in ('Zeitung', 'Freiheit', 'Gesellschaft', 'Information', 'Universität', 'Frühling',
                     'Eigentum', 'Datum', 'Ursprung', 'Großhandel', 'Aktionär'):
            self.assertRule(word, Fuge(add='s'))
        for word in ('Tourist', 'Jurist', 'Polizist', 'Gitarrist', 'Atheist', 'Egoist', 'Mitmensch'):
            self.assertRule(word, Fuge(add='en'))
        for word in ('Biologe', 'Pädagoge', 'Hausnummer'):
            self.assertRule(word, Fuge(add='n'))
        for word in ('Lehrerin', 'Studentin', 'Sekretärin', 'Autorin'):
            self.assertRule(word, Fuge(strip='in', add='innen'))
        for word in ('Jugendlicher', 'Delegierter', 'Beschäftigter'):
            self.assertRule(word, Fuge(strip='r', add='n'))
        for word in ('Mädchen', 'Lehrer', 'Apfel', 'Musik', 'Kultur', 'Kaffee', 'Glas', 'Tisch',
                     'Therapie', 'Demokratie', 'Analyse'):
            self.assertRule(word, NONE)

    def test_words_that_only_look_like_a_rule(self):
        # Sprung is no -ung word and Stadion no -ion word, in compounds as well
        for word in ('Kopfsprung', 'Aufschwung', 'Stadion', 'Türspion'):
            self.assertRule(word, NONE)
        # compounds of Frist, Geist, List and Mist are no people on -ist
        for word in ('Abgabefrist', 'Zeitgeist', 'Arglist', 'Bockmist'):
            self.assertRule(word, NONE)

    def test_ending_must_be_a_suffix(self):
        for word in ('Sprung', 'Frist', 'Tee', 'Faktum', 'Prämie', 'Geschäftsidee', 'Nitroglycerin'):
            self.assertIsNone(by_rule(word), word)


class FugenTest(unittest.TestCase):

    def setUp(self):
        self.fugen = Fugen([
            'Sonne', 'Blume', 'Schein', 'Brille', 'Sonnenblume', 'Sonnenschein', 'Sonnenbrille',
            'Schule', 'Hof', 'Buch', 'Schulhof', 'Schulbuch', 'Busfahrer', 'Schulbusfahrer',
            'Haus', 'Haue', 'Mittel', 'Hausmittel',
            'Aue', 'Gang', 'Ausgang', 'Ausgangssperre', 'Sperre',
            'Zustand', 'Vorstand', 'Bestand', 'Wohlstand', 'Wechsel', 'Sitzung', 'Aufnahme',
            'Zustandswechsel', 'Vorstandssitzung', 'Bestandsaufnahme',
            'Firma', 'Wagen', 'Name', 'Firmenwagen', 'Firmenname',
            'NATO', 'Garten', 'Pferd',
            'Strand', 'Korb', 'Strandkorb', 'Rand', 'Stein', 'Randstein',
            'Gebiet', 'Reform', 'Gebietsreform', 'Grenze', 'Grenzgebiet',
            'Seite', 'Straße', 'Bahn', 'Straßenbahn', 'Seitenstraße',
            'Kunde', 'Karte', 'Kundenkarte', 'Erde', 'Erdkunde', 'Erdkundebuch', 'Heimat', 'Heimatkunde',
        ])

    def test_attested(self):
        self.assertEqual(self.fugen.decide('Sonne'), (Fuge(add='n'), 'attested'))
        self.assertEqual(self.fugen.first_part('Sonne'), 'Sonnen')
        self.assertEqual(self.fugen.first_part('Schule'), 'Schul')
        self.assertEqual(self.fugen.first_part('Firma'), 'Firmen')

    def test_stem_change_only_if_needed(self):
        # Hausmittel is Haus + Mittel, not Haue - e + s + Mittel
        self.assertEqual(self.fugen.decide('Haus'), (NONE, 'attested'))
        self.assertNotIn('haue', self.fugen.attested)

    def test_particles_are_no_nouns(self):
        # Ausgang is aus + Gang, not Aue - e + s + Gang
        self.assertNotIn('aue', self.fugen.attested)
        self.assertIsNone(self.fugen.decide('Aue'))

    def test_rule(self):
        self.assertEqual(self.fugen.decide('Zeitung'), (Fuge(add='s'), 'rule'))
        self.assertEqual(self.fugen.first_part('Zeitung'), 'Zeitungs')

    def test_analogy(self):
        # Zustand, Vorstand and Bestand all take an s
        self.assertEqual(self.fugen.decide('Wohlstand'), (Fuge(add='s'), 'analogy'))
        self.assertEqual(self.fugen.first_part('Wohlstand'), 'Wohlstands')

    def test_conflicting_analogy_leaves_word_out(self):
        # words on -and disagree: Zustand, Vorstand, Bestand +s, but Strand and Rand none
        self.assertIsNone(self.fugen.decide('Verband'))

    def test_head(self):
        # a compound links like its last part
        self.assertEqual(self.fugen.decide('Grenzgebiet'), (Fuge(add='s'), 'head'))
        self.assertEqual(self.fugen.first_part('Seitenstraße'), 'Seitenstraßen')
        # unless the words ending like it disagree (Kunde +n, Erdkunde none)
        self.assertIsNone(self.fugen.decide('Heimatkunde'))

    def test_abbreviation(self):
        self.assertEqual(self.fugen.decide('NATO'), (NONE, 'abbreviation'))
        self.assertEqual(self.fugen.decide('CO2'), (NONE, 'abbreviation'))
        self.assertEqual(self.fugen.decide('iPhone'), (NONE, 'abbreviation'))
        self.assertEqual(self.fugen.decide('LehrerIn'), (NONE, 'abbreviation'))

    def test_abbreviation_is_not_taken_for_a_word(self):
        fugen = Fugen(['Leder', 'Jacke', 'Mantel', 'Lederjacke', 'Ledermantel', 'LED'])
        self.assertEqual(fugen.decide('LED'), (NONE, 'abbreviation'))

    def test_stem_change_needs_two_compounds(self):
        # Imme - e + Unität is really Immunität, Opa - a + en + Source is Opensource
        self.assertNotIn('imme', Fugen(['Imme', 'Unität', 'Immunität']).attested)
        self.assertNotIn('opa', Fugen(['Opa', 'Source', 'Opensource']).attested)

    def test_fallback(self):
        self.assertEqual(self.fugen.decide('Pferd'), (NONE, 'fallback'))
        # words on -e are too unpredictable without a hint
        self.assertIsNone(self.fugen.decide('Garage'))
        self.assertIsNone(self.fugen.first_part('Garage'))

    def test_explain(self):
        self.assertEqual(self.fugen.explain('Sonne'), 'Sonne -> Sonnen (+n, attested in 3 compounds)')
        self.assertEqual(self.fugen.explain('Garage'), 'Garage: left out, linking element unclear')
        self.assertIn('Wohlstand -> Wohlstands (+s, analogy to words ending in -stand', self.fugen.explain('Wohlstand'))


if __name__ == '__main__':
    unittest.main()
