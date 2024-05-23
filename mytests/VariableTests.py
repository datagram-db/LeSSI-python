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


    def test_init(self):
        self.assertTrue(hasattr(self.kb, "g"), "The attribute g within kb should contain the information for the...")
        self.assertTrue(hasattr(self.kb.g, "name_eq"), "The knowledge base of choice should support the name_eq method")

    def test_names(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        self.assertEqual(self.kb.g.name_eq("genoveffo", "genoveffo"), CasusHappening.EQUIVALENT, "Two arbitrary names should be always equivalent")
        self.assertEqual(self.kb.g.name_eq("Saturdays", None), CasusHappening.INDIFFERENT, "A name always implies a missing name (loss of information)")
        self.assertEqual(self.kb.g.name_eq(None, "Saturdays"), CasusHappening.MISSING_1ST_IMPLICATION, "If I have no information, I cannot be more precise than this")
        self.assertEqual(self.kb.g.name_eq("city", "Newcastle"), CasusHappening.GENERAL_IMPLICATION, "If something happens in cities, then it should also happen in Newcastle, but not viceversa")


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
        self.assertEqual(d[(self.Saturdays,None)], CasusHappening.INDIFFERENT, "A name always implies a missing name (loss of information)")
        self.assertEqual(d[(self.Saturdays, self.aNone)], CasusHappening.INDIFFERENT,
                         "A name always implies a missing name (loss of information)")

        compare_variable(d,  None,self.Saturdays, self.kb.g)
        compare_variable(d,  self.aNone,self.Saturdays, self.kb.g)
        self.assertEqual(d[(None,self.Saturdays)], CasusHappening.MISSING_1ST_IMPLICATION, "A name always implies a missing name (loss of information)")
        self.assertEqual(d[( self.aNone,self.Saturdays)], CasusHappening.MISSING_1ST_IMPLICATION,
                         "A name always implies a missing name (loss of information)")

    def test_variable_with_cop(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        from Parmenides.TBox.ExpandConstituents import compare_variable

        d = dict()
        compare_variable(d, self.ft, self.t, self.kb.g)
        self.assertEqual(d[self.ft, self.t], CasusHappening.LOSE_SPEC_IMPLICATION, "The COP has a similar function to the specification")
        compare_variable(d, self.st, self.t, self.kb.g)
        self.assertEqual(d[self.st, self.t], CasusHappening.LOSE_SPEC_IMPLICATION, "The COP has a similar function to the specification")
        compare_variable(d, self.st, self.ft, self.kb.g)
        self.assertEqual(d[self.st, self.ft], CasusHappening.EXCLUSIVES,
                         "The COP has a similar function to the specification")

    def test_variable_with_specification(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        from Parmenides.TBox.ExpandConstituents import compare_variable

        d = dict()
        compare_variable(d, self.ncc, self.Newcastle, self.kb.g)
        self.assertEqual(d[(self.ncc, self.Newcastle)], CasusHappening.INDIFFERENT,
                         "The specification should provide a notion of specifcation towards generalisation (missing specification)")
        compare_variable(d, self.Newcastle, self.ncc, self.kb.g)
        self.assertEqual(d[(self.Newcastle, self.ncc)], CasusHappening.INSTANTIATION_IMPLICATION, "The specification should provide a notion of specifcation towards generalisation (missing specification)")
        compare_variable(d, self.ncc, self.cc, self.kb.g)
        self.assertEqual(d[(self.ncc,self.cc)], CasusHappening.INDIFFERENT, "The specification is an entity refining another entity with a stronger type")
        compare_variable(d, self.cc, self.ncc, self.kb.g)
        self.assertEqual(d[(self.cc, self.ncc)], CasusHappening.INSTANTIATION_IMPLICATION, "The specification is an entity refining another entity with a stronger type")


    def test_unary(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        from Parmenides.TBox.ExpandConstituents import test_pairwise_sentence_similarity
        from logical_repr.rewrite_kernels import make_unary

        d = dict()
        btncc = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.ncc])})
        btnotncc = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.nncc])})
        test_pairwise_sentence_similarity(d, btncc, btnotncc, kb=self.kb.g)
        self.assertEqual(d[(btncc, btnotncc)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d,  btnotncc, btncc, kb=self.kb.g)
        self.assertEqual(d[(btnotncc, btncc)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")

        from logical_repr.rewrite_kernels import make_unary
        from logical_repr.Sentences import FUnaryPredicate
        btfn = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        btsn = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        bttn = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        ntsncc = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.ncc])}.items()))
        test_pairwise_sentence_similarity(d, btfn, bttn, kb=self.kb.g)
        self.assertEqual(d[(btfn, bttn)], CasusHappening.LOSE_SPEC_IMPLICATION,
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
        self.assertEqual(d[(ntfncc, bttn)], CasusHappening.INDIFFERENT,
                         "Maximum reduction by stripping all information, both adjective and specification")
        ntsn = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        test_pairwise_sentence_similarity(d, ntsn, ntfncc, kb=self.kb.g)
        test_pairwise_sentence_similarity(d, ntfncc, ntsn, kb=self.kb.g)
        self.assertEqual(d[(ntfncc, ntsn)], CasusHappening.EXCLUSIVES,
                         "Implication is blocked by inequality, that should dominate (in this case) rather than providing unknowingness")
        self.assertEqual(d[(ntsn, ntfncc)], CasusHappening.EXCLUSIVES,
                         "Implication is blocked by inequality, that should dominate (in this case) rather than providing unknowingness")
        #ntfncc, btfn
        test_pairwise_sentence_similarity(d, ntfncc, btfn, kb=self.kb.g)
        self.assertEqual(d[(ntfncc, btfn)], CasusHappening.INDIFFERENT,
                         "If the arguments are the same but the properties are indifferent, then you should reflect the latter")

        ftN = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.Newcastle])}.items()))
        ftncc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.ncc])}.items()))
        test_pairwise_sentence_similarity(d, ftN, ftncc, kb=self.kb.g)
        self.assertEqual(d[(ftN, ftncc)], CasusHappening.INSTANTIATION_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftncc, ftN, kb=self.kb.g)
        self.assertEqual(d[(ftncc, ftN)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")

        btN = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.Newcastle])}.items()))
        btNcc = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.ncc])}.items()))
        test_pairwise_sentence_similarity(d, ftncc, btN, kb=self.kb.g)
        self.assertEqual(d[(ftncc, btN)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")

        ftcc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.cc])}.items()))
        test_pairwise_sentence_similarity(d, ftcc, ntfncc, kb=self.kb.g)
        self.assertEqual(d[(ftcc, ntfncc)], CasusHappening.INSTANTIATION_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftcc, btNcc, kb=self.kb.g)
        self.assertEqual(d[(ftcc, btNcc)], CasusHappening.INSTANTIATION_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftN, btNcc, kb=self.kb.g)
        self.assertEqual(d[(ftN, btNcc)], CasusHappening.INSTANTIATION_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, btNcc, ftN, kb=self.kb.g)
        self.assertEqual(d[(btNcc, ftN)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")

    def test_unary_timeright(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        from Parmenides.TBox.ExpandConstituents import test_pairwise_sentence_similarity

        d = dict()
        from logical_repr.rewrite_kernels import make_unary
        btncc = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.ncc])})
        btnotncc = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.nncc])})
        btncc_d = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])})
        btnotncc_d = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.nncc]),"TIME": tuple([self.Saturdays])})
        from logical_repr.Sentences import FUnaryPredicate
        btfn = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        btsn = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        bttn = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        ntsncc = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.ncc])}.items()))
        ntfncc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.ncc])}.items()))
        ntsn = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        ftN = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.Newcastle])}.items()))
        ftncc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.ncc])}.items()))
        btN = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.Newcastle])}.items()))
        btNcc = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.ncc])}.items()))
        ftcc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.cc])}.items()))
        btfn_d = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        btsn_d = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        bttn_d = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE":tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        ntsncc_d = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        ntfncc_d = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        ntsn_d = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        ftN_d = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        ftncc_d = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        btN_d = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        btNcc_d = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        ftcc_d = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.cc]),"TIME": tuple([self.Saturdays])}.items()))

        ## All the previous tests leading to an inconsistency or to an indifference being extended by adding the time
        ## only on the rightmost argument, then should always lead to the same result
        test_pairwise_sentence_similarity(d, bttn, btfn_d, kb=self.kb.g)
        self.assertEqual(d[( bttn, btfn_d)], CasusHappening.INDIFFERENT,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, btsn, btfn_d, kb=self.kb.g)
        self.assertEqual(d[( btsn, btfn_d)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, btfn, btsn_d, kb=self.kb.g)
        self.assertEqual(d[( btfn,btsn_d)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, ntfncc, ntsn_d, kb=self.kb.g)
        self.assertEqual(d[(ntfncc, ntsn_d)], CasusHappening.EXCLUSIVES,
                         "Implication is blocked by inequality, that should dominate (in this case) rather than providing unknowingness")
        test_pairwise_sentence_similarity(d, ntsn, ntfncc_d, kb=self.kb.g)
        self.assertEqual(d[(ntsn, ntfncc_d)], CasusHappening.EXCLUSIVES,
                         "Implication is blocked by inequality, that should dominate (in this case) rather than providing unknowingness")
        test_pairwise_sentence_similarity(d, ftncc, ftN_d, kb=self.kb.g)
        self.assertEqual(d[(ftncc, ftN_d)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ntfncc, bttn_d, kb=self.kb.g)
        self.assertEqual(d[(ntfncc, bttn_d)], CasusHappening.INDIFFERENT,
                         "Maximum reduction by stripping all information, both adjective and specification")

        test_pairwise_sentence_similarity(d, ntfncc, btfn_d, kb=self.kb.g)
        self.assertEqual(d[(ntfncc, btfn_d)], CasusHappening.INDIFFERENT,
                         "If the arguments are the same but the properties are indifferent, then you should reflect the latter")

        test_pairwise_sentence_similarity(d, btNcc, ftN_d, kb=self.kb.g)
        self.assertEqual(d[(btNcc, ftN_d)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")


        test_pairwise_sentence_similarity(d, btfn, bttn_d, kb=self.kb.g)
        self.assertEqual(d[(btfn, bttn_d)], CasusHappening.GENERAL_IMPLICATION,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")

        # print(str(ftcc)+" vs. "+str(ntfncc_d))
        test_pairwise_sentence_similarity(d, ftcc, ntfncc_d, kb=self.kb.g)
        self.assertEqual(d[(ftcc, ntfncc_d)], CasusHappening.GENERAL_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftN, ftncc_d, kb=self.kb.g)
        self.assertEqual(d[(ftN, ftncc_d)], CasusHappening.GENERAL_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftN, btNcc_d, kb=self.kb.g)
        self.assertEqual(d[(ftN, btNcc_d)], CasusHappening.GENERAL_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftncc, btN_d, kb=self.kb.g)
        self.assertEqual(d[(ftncc, btN_d)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftcc, btNcc_d, kb=self.kb.g)
        self.assertEqual(d[(ftcc, btNcc_d)], CasusHappening.GENERAL_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")


    def test_unary_timeleft(self):
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        from Parmenides.TBox.ExpandConstituents import test_pairwise_sentence_similarity

        d = dict()
        from logical_repr.rewrite_kernels import make_unary
        btncc = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.ncc])})
        btnotncc = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.nncc])})
        btncc_d = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])})
        btnotncc_d = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.nncc]),"TIME": tuple([self.Saturdays])})
        from logical_repr.Sentences import FUnaryPredicate
        btfn = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        btsn = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        bttn = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        ntsncc = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.ncc])}.items()))
        ntfncc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.ncc])}.items()))
        ntsn = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle])}.items()))
        ftN = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.Newcastle])}.items()))
        ftncc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.ncc])}.items()))
        btN = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.Newcastle])}.items()))
        btNcc = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.ncc])}.items()))
        ftcc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.cc])}.items()))
        btfn_d = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        btsn_d = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        bttn_d = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE":tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        ntsncc_d = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        ntfncc_d = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE":tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        ntsn_d = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE":tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        ftN_d = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        ftncc_d = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        btN_d = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        btNcc_d = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        ftcc_d = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.cc]),"TIME": tuple([self.Saturdays])}.items()))

        ## All the previous tests leading to an inconsistency or to an indifference being extended by adding the time
        ## only on the rightmost argument, then should always lead to the same result
        test_pairwise_sentence_similarity(d, bttn_d, btfn, kb=self.kb.g)
        self.assertEqual(d[( bttn_d, btfn)], CasusHappening.INDIFFERENT,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, btsn_d, btfn, kb=self.kb.g)
        self.assertEqual(d[( btsn_d, btfn)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, btfn_d, btsn, kb=self.kb.g)
        self.assertEqual(d[( btfn_d,btsn)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, ntfncc_d, ntsn, kb=self.kb.g)
        self.assertEqual(d[(ntfncc_d, ntsn)], CasusHappening.EXCLUSIVES,
                         "Implication is blocked by inequality, that should dominate (in this case) rather than providing unknowingness")
        test_pairwise_sentence_similarity(d, ntsn_d, ntfncc, kb=self.kb.g)
        self.assertEqual(d[(ntsn_d, ntfncc)], CasusHappening.EXCLUSIVES,
                         "Implication is blocked by inequality, that should dominate (in this case) rather than providing unknowingness")
        test_pairwise_sentence_similarity(d, ftncc_d, ftN, kb=self.kb.g)
        self.assertEqual(d[(ftncc_d, ftN)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ntfncc_d, bttn, kb=self.kb.g)
        self.assertEqual(d[(ntfncc_d, bttn)], CasusHappening.INDIFFERENT,
                         "Maximum reduction by stripping all information, both adjective and specification")
        test_pairwise_sentence_similarity(d, ntfncc_d, btfn, kb=self.kb.g)
        self.assertEqual(d[(ntfncc_d, btfn)], CasusHappening.INDIFFERENT,
                         "If the arguments are the same but the properties are indifferent, then you should reflect the latter")
        test_pairwise_sentence_similarity(d, btNcc_d, ftN, kb=self.kb.g)
        self.assertEqual(d[(btNcc_d, ftN)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftncc_d, btN, kb=self.kb.g)
        self.assertEqual(d[(ftncc_d, btN)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, btfn_d, bttn, kb=self.kb.g)
        self.assertEqual(d[(btfn_d, bttn)], CasusHappening.INDIFFERENT,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, ftN_d, btNcc, kb=self.kb.g)
        self.assertEqual(d[(ftN_d, btNcc)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftcc_d, btNcc, kb=self.kb.g)
        self.assertEqual(d[(ftcc_d, btNcc)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")


        test_pairwise_sentence_similarity(d, ftN_d, ftncc, kb=self.kb.g)
        self.assertEqual(d[(ftN_d, ftncc)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftcc_d, ntfncc, kb=self.kb.g)
        self.assertEqual(d[(ftcc_d, ntfncc)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")


    def test_unary_alltime_location(self):
        #
        from Parmenides.TBox.ExpandConstituents import CasusHappening
        from Parmenides.TBox.ExpandConstituents import test_pairwise_sentence_similarity
        from logical_repr.rewrite_kernels import make_not, make_cop, make_unary

        d = dict()
        btncc = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])})
        btnotncc = make_unary("be", self.t, 1.0, prop={"GPE": tuple([self.nncc]),"TIME": tuple([self.Saturdays])})
        test_pairwise_sentence_similarity(d, btncc, btnotncc, kb=self.kb.g)
        self.assertEqual(d[(btncc, btnotncc)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, btnotncc, btncc, kb=self.kb.g)
        self.assertEqual(d[(btnotncc, btncc)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")

        from logical_repr.rewrite_kernels import make_unary
        from logical_repr.Sentences import FUnaryPredicate
        btfn = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        btsn = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE": tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        bttn = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        ntsncc = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        test_pairwise_sentence_similarity(d, btfn, bttn, kb=self.kb.g)
        self.assertEqual(d[(btfn, bttn)], CasusHappening.LOSE_SPEC_IMPLICATION,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, bttn, btfn, kb=self.kb.g)
        self.assertEqual(d[(bttn, btfn)], CasusHappening.INDIFFERENT,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, btsn, btfn, kb=self.kb.g)
        self.assertEqual(d[(btsn, btfn)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        test_pairwise_sentence_similarity(d, btfn, btsn, kb=self.kb.g)
        self.assertEqual(d[(btfn, btsn)], CasusHappening.EXCLUSIVES,
                         "Negation of the specification where the rest is the same should yield to an incompatibility")
        ntfncc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        test_pairwise_sentence_similarity(d, ntfncc, bttn, kb=self.kb.g)
        self.assertEqual(d[(ntfncc, bttn)], CasusHappening.INDIFFERENT,
                         "Maximum reduction by stripping all information, both adjective and specification")
        ntsn = FUnaryPredicate("be", self.st, 1.0, frozenset({"GPE": tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        test_pairwise_sentence_similarity(d, ntfncc, ntsn, kb=self.kb.g)
        test_pairwise_sentence_similarity(d, ntsn, ntfncc, kb=self.kb.g)
        self.assertEqual(d[(ntfncc, ntsn)], CasusHappening.EXCLUSIVES,
                         "Implication is blocked by inequality, that should dominate (in this case) rather than providing unknowingness")
        self.assertEqual(d[(ntsn, ntfncc)], CasusHappening.EXCLUSIVES,
                         "Implication is blocked by inequality, that should dominate (in this case) rather than providing unknowingness")
        # ntfncc, btfn
        test_pairwise_sentence_similarity(d, ntfncc, btfn, kb=self.kb.g)
        self.assertEqual(d[(ntfncc, btfn)], CasusHappening.INDIFFERENT,
                         "If the arguments are the same but the properties are indifferent, then you should reflect the latter")

        ftN = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        ftncc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        test_pairwise_sentence_similarity(d, ftN, ftncc, kb=self.kb.g)
        self.assertEqual(d[(ftN, ftncc)], CasusHappening.INSTANTIATION_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftncc, ftN, kb=self.kb.g)
        self.assertEqual(d[(ftncc, ftN)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")

        btN = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.Newcastle]),"TIME": tuple([self.Saturdays])}.items()))
        btNcc = FUnaryPredicate("be", self.t, 1.0, frozenset({"GPE": tuple([self.ncc]),"TIME": tuple([self.Saturdays])}.items()))
        test_pairwise_sentence_similarity(d, ftncc, btN, kb=self.kb.g)
        self.assertEqual(d[(ftncc, btN)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")

        ftcc = FUnaryPredicate("be", self.ft, 1.0, frozenset({"GPE": tuple([self.cc]),"TIME": tuple([self.Saturdays])}.items()))
        test_pairwise_sentence_similarity(d, ftcc, ntfncc, kb=self.kb.g)
        self.assertEqual(d[(ftcc, ntfncc)], CasusHappening.INSTANTIATION_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftcc, btNcc, kb=self.kb.g)
        self.assertEqual(d[(ftcc, btNcc)], CasusHappening.INSTANTIATION_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, ftN, btNcc, kb=self.kb.g)
        self.assertEqual(d[(ftN, btNcc)], CasusHappening.INSTANTIATION_IMPLICATION,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")
        test_pairwise_sentence_similarity(d, btNcc, ftN, kb=self.kb.g)
        self.assertEqual(d[(btNcc, ftN)], CasusHappening.INDIFFERENT,
                         "Notwithstanding that the argument are not generally implying themselves, when dealing with predicate implication then we need to consider ")



if __name__ == '__main__':
    unittest.main()