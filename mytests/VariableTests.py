import unittest

class VariableTests(unittest.TestCase):


    def setUp(self):
        from Parmenides.TBox.CrossMatch import DoExpand
        self.kb = DoExpand('../Parmenides/turtle.ttl', '../Parmenides/TBox/file.txt')
        from logical_repr.Sentences import make_name
        from logical_repr.rewrite_kernels import make_not,make_cop,make_unary
        self.genoveffo = make_name("genoveffo")
        self.aNone = make_name(None)
        self.Saturdays = make_name("Saturdays")
        self.city = make_name("city")
        self.cc = make_name("city center")
        self.t = make_name("traffic")
        self.Newcastle = make_name("Newcastle")
        self.ncc = make_name("Newcastle", spec="city center")
        self.fast = make_cop("fast")
        self.slow = make_cop("slow")
        self.ft = make_name("traffic", cop=self.fast)
        self.st = make_name("traffic", cop=self.slow)
        self.nncc = make_not(self.ncc)
        self.btncc = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.ncc])})
        self.btnotncc = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.nncc])})

    def test_init(self):
        self.assertTrue(hasattr(self.kb, "g"), "The attribute g within kb should contain the information for the...")
        self.assertTrue(hasattr(self.kb.g, "name_eq"), "The knowledge base of choice should support the name_eq method")

    def test_names(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        self.assertEqual(self.kb.g.name_eq("genoveffo", "genoveffo"), CasusHappening.EQUIVALENT, "Two arbitrary names should be always equivalent")
        self.assertEqual(self.kb.g.name_eq("Saturdays", None), CasusHappening.IMPLICATION, "A name always implies a missing name (loss of information)")
        self.assertEqual(self.kb.g.name_eq(None, "Saturdays"), CasusHappening.INDIFFERENT, "If I have no information, I cannot be more precise than this")
        self.assertEqual(self.kb.g.name_eq("city", "Newcastle"), CasusHappening.IMPLICATION, "If something happens in cities, then it should also happen in Newcastle, but not viceversa")


    def test_variables_as_names(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        from Parmenides.TBox.ExpandConstituents import compare_variable

        d = dict()
        var = compare_variable(d, self.genoveffo, self.genoveffo, self.kb.g)
        self.assertEqual(d[(self.genoveffo,self.genoveffo)], var, "The map should have been populated")
        self.assertEqual(d[(self.genoveffo,self.genoveffo)], CasusHappening.EQUIVALENT, "Two arbitrary names should be always equivalent")

        compare_variable(d, self.fast, self.slow, self.kb.g)
        compare_variable(d, self.slow, self.fast, self.kb.g)
        self.assertEqual(d[(self.fast,self.slow)], CasusHappening.EXCLUSIVES, "Understanding opposing adjectives")
        self.assertEqual(d[(self.slow,self.fast)], CasusHappening.EXCLUSIVES, "Understanding opposing adjectives")


        compare_variable(d, self.Saturdays, None, self.kb.g)
        compare_variable(d, self.Saturdays, self.aNone, self.kb.g)
        self.assertEqual(d[(self.Saturdays,None)], CasusHappening.IMPLICATION, "A name always implies a missing name (loss of information)")
        self.assertEqual(d[(self.Saturdays, self.aNone)], CasusHappening.IMPLICATION,
                         "A name always implies a missing name (loss of information)")

        compare_variable(d,  None,self.Saturdays, self.kb.g)
        compare_variable(d,  self.aNone,self.Saturdays, self.kb.g)
        self.assertEqual(d[(None,self.Saturdays)], CasusHappening.INDIFFERENT, "A name always implies a missing name (loss of information)")
        self.assertEqual(d[( self.aNone,self.Saturdays)], CasusHappening.INDIFFERENT,
                         "A name always implies a missing name (loss of information)")

    def test_variable_with_cop(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        from Parmenides.TBox.ExpandConstituents import compare_variable

        d = dict()
        compare_variable(d, self.ft, self.t, self.kb.g)
        self.assertEqual(d[self.ft, self.t], CasusHappening.IMPLICATION, "The COP has a similar function to the specification")
        compare_variable(d, self.st, self.t, self.kb.g)
        self.assertEqual(d[self.st, self.t], CasusHappening.IMPLICATION, "The COP has a similar function to the specification")
        compare_variable(d, self.st, self.ft, self.kb.g)
        self.assertEqual(d[self.st, self.ft], CasusHappening.EXCLUSIVES,
                         "The COP has a similar function to the specification")

    def test_variable_with_specification(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        from Parmenides.TBox.ExpandConstituents import compare_variable

        d = dict()
        compare_variable(d, self.ncc, self.Newcastle, self.kb.g)
        self.assertEqual(d[(self.ncc, self.Newcastle)], CasusHappening.IMPLICATION, "The specification should provide a notion of specifcation towards generalisation (missing specification)")
        compare_variable(d, self.Newcastle, self.ncc, self.kb.g)
        self.assertEqual(d[(self.Newcastle, self.ncc)], CasusHappening.INDIFFERENT, "The specification should provide a notion of specifcation towards generalisation (missing specification)")
        compare_variable(d, self.cc, self.ncc, self.kb.g)
        self.assertEqual(d[(self.cc, self.ncc)], CasusHappening.IMPLICATION, "The specification is an entity refining another entity with a stronger type")
        compare_variable(d, self.ncc, self.cc, self.kb.g)
        self.assertEqual(d[(self.ncc,self.cc)], CasusHappening.INDIFFERENT, "The specification is an entity refining another entity with a stronger type")


    def test_unary_negation(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        from Parmenides.TBox.ExpandConstituents import test_pairwise_sentence_similarity

        d = dict()
        test_pairwise_sentence_similarity(d, self.btncc, self.btnotncc, kb=self.kb.g)
        self.assertEqual(d[(self.btncc, self.btnotncc)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d,  self.btnotncc, self.btncc, kb=self.kb.g)
        self.assertEqual(d[(self.btnotncc, self.btncc)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")

        from logical_repr.rewrite_kernels import make_unary
        from logical_repr.Sentences import FUnaryPredicate
        btfn = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        btsn = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        bttn = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        test_pairwise_sentence_similarity(d, btfn, bttn, kb=self.kb.g)
        self.assertEqual(d[(btfn, bttn)], CasusHappening.IMPLICATION,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, bttn, btfn, kb=self.kb.g)
        self.assertEqual(d[( bttn, btfn)], CasusHappening.INDIFFERENT,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, btsn, btfn, kb=self.kb.g)
        self.assertEqual(d[( btsn, btfn)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, btfn, btsn, kb=self.kb.g)
        self.assertEqual(d[( btfn,btsn)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        ntfncc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.ncc])}.items()))
        test_pairwise_sentence_similarity(d, ntfncc, bttn, kb=self.kb.g)
        self.assertEqual(d[(ntfncc, bttn)], CasusHappening.IMPLICATION,
                         "Maximum reduction by stripping all information, both adjective and specification")

if __name__ == '__main__':
    unittest.main()