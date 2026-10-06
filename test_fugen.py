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


class RuleTest(unittest.TestCase):

    def assertRule(self, word, fuge):
        rule = by_rule(word)
        self.assertIsNotNone(rule, word)
        self.assertEqual(rule[0], fuge, word)

    def test_rules(self):
        for word in ('Zeitung', 'Freiheit', 'Gesellschaft', 'Information', 'Universität', 'Frühling'):
            self.assertRule(word, Fuge(add='s'))
        for word in ('Tourist', 'Jurist', 'Polizist'):
            self.assertRule(word, Fuge(add='en'))
        self.assertRule('Lehrerin', Fuge(strip='in', add='innen'))
        for word in ('Mädchen', 'Lehrer', 'Apfel', 'Musik', 'Kultur', 'Kaffee', 'Glas', 'Tisch'):
            self.assertRule(word, NONE)

    def test_ending_must_be_a_suffix(self):
        self.assertIsNone(by_rule('Sprung'))
        self.assertIsNone(by_rule('Frist'))
        self.assertIsNone(by_rule('Tee'))


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

    def test_abbreviation(self):
        self.assertEqual(self.fugen.decide('NATO'), (NONE, 'abbreviation'))
        self.assertEqual(self.fugen.decide('CO2'), (NONE, 'abbreviation'))

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
