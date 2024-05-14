import json

from antlr4 import *

from Parmenides.TBox.SentenceMatch import RWVariable
from logical_repr.Sentences import Formula
from parmenides_tboxParser import parmenides_tboxParser
from parmenides_tboxLexer import parmenides_tboxLexer
from parmenides_tboxVisitor import parmenides_tboxVisitor

def unfold_string(d):
    if hasattr(d, "text"):
        d = d.text.strip()
    elif hasattr(d, "getText") and callable(getattr(d, "getText", None)):
        d = d.getText().strip()
    else:
        raise ValueError("Unexpected type: "+type(d).__name__+" for: "+str(d))
    if d == "none":
        return None
    return json.loads(d)



class CommonComponents:
    def __init__(self, ontology_query, replacement_pair, operations):
        self.operations = operations
        self.replacement_pair = replacement_pair
        self.ontology_query = ontology_query

class UpdateOperation:
    cc:CommonComponents
    formula:Formula
    def __init__(self, formula, cc:CommonComponents):
        self.cc = cc
        self.formula = formula

class RewriteOperation:
    cc:CommonComponents
    match:Formula
    rewrite:Formula
    def __init__(self, match, rewrite, cc:CommonComponents):
        self.cc = cc
        self.match = match
        self.rewrite = rewrite

class TBoxVisitor(parmenides_tboxVisitor):


    def visit(self, tree):
        if tree is None:
            return None
        else:
            return super().visit(tree)

    def common_class_expand(self, ctx):
        if ctx is None:
            return None
        ontology_query = self.visit(ctx.ontology_query())
        replacement_pair = [self.visit(x) for x in ctx.replacement_pair()]
        operations = [self.visit(x) for x in ctx.operations()]
        return CommonComponents(ontology_query, replacement_pair, operations)

    def visitParmenides_tbox(self, ctx: parmenides_tboxParser.Parmenides_tboxContext):
        return [self.visit(x) for x in ctx.rule_()]

    def visitSubstitutions(self, ctx: parmenides_tboxParser.SubstitutionsContext):
        if ctx is None:
            return None
        cc = self.common_class_expand(ctx)
        return UpdateOperation(self.visit(ctx.formula()), cc)

    def visitInvention(self, ctx: parmenides_tboxParser.InventionContext):
        if ctx is None:
            return None
        cc = self.common_class_expand(ctx)
        return RewriteOperation(self.visit(ctx.formula(0)), self.visit(ctx.formula(1)), cc)

    def visitFparen(self, ctx: parmenides_tboxParser.FparenContext):
        return self.visit(ctx.formula())

    def visitRw_variable(self, ctx: parmenides_tboxParser.Rw_variableContext):
        if ctx is None:
            return None
        return RWVariable(unfold_string(ctx.STRING()))

    def visitVariable(self, ctx: parmenides_tboxParser.VariableContext):
        if ctx is None:
            return None
        name = unfold_string(ctx.name)
        type_ = unfold_string(ctx.type_)
        specification = unfold_string(ctx.specification)
        cop = self.visit(ctx.formula())
        from logical_repr.Sentences import FVariable
        return FVariable(name, type_, specification, cop)

    def visitUnary_predicate(self, ctx: parmenides_tboxParser.Unary_predicateContext):
        if ctx is None:
            return None
        rel = unfold_string(ctx.rel)
        src = self.visit(ctx.arg)
        score = float(ctx.score)
        properties = frozenset(dict([self.visit(x) for x in ctx.key_values()]).items())
        from logical_repr.Sentences import FBinaryPredicate
        from logical_repr.Sentences import FUnaryPredicate
        return FUnaryPredicate(rel, src, score, properties)
    def visitBinary_predicate(self, ctx: parmenides_tboxParser.Binary_predicateContext):
        if ctx is None:
            return None
        rel = unfold_string(ctx.rel)
        src = self.visit(ctx.src)
        dst = self.visit(ctx.dst)
        score = float(unfold_string(ctx.score))
        properties = frozenset(dict([self.visit(x) for x in ctx.key_values()]).items())
        from logical_repr.Sentences import FBinaryPredicate
        return FBinaryPredicate(rel, src, dst, score, properties)

    def visitAnd(self, ctx: parmenides_tboxParser.AndContext):
        from logical_repr.Sentences import FAnd
        return FAnd(args=tuple([self.visit(x) for x in ctx.formula()]))

    def visitOr(self, ctx: parmenides_tboxParser.OrContext):
        from logical_repr.Sentences import FOr
        return FOr(args=tuple([self.visit(x) for x in ctx.formula()]))

    def visitNot(self, ctx: parmenides_tboxParser.NotContext):
        from logical_repr.Sentences import FNot
        return FNot(self.visit(ctx.formula()))

    def visitRemove(self, ctx: parmenides_tboxParser.RemoveContext):
        from logical_repr.Sentences import RemovePropertiesFromResult
        return RemovePropertiesFromResult(unfold_string(ctx.STRING()))

    def visitAdd(self, ctx: parmenides_tboxParser.AddContext):
        from logical_repr.Sentences import AddPropertyFromResult
        return AddPropertyFromResult(ofField=unfold_string(ctx.STRING()),toAddInFields=self.visit(ctx.formula()))

    def visitAll_properties(self, ctx: parmenides_tboxParser.All_propertiesContext):
        from logical_repr.Sentences import InheritProperties
        return InheritProperties()

    def visitEdge_match(self, ctx: parmenides_tboxParser.Edge_matchContext):
        return [unfold_string(x) for x in ctx.STRING()]

    def visitIsa_match(self, ctx: parmenides_tboxParser.Isa_matchContext):
        return [unfold_string(x) for x in ctx.STRING()]

    def visitAll_queries(self, ctx: parmenides_tboxParser.All_queriesContext):
        return tuple(["and", [self.visit(x) for x in ctx.ontology_query()]])

    def visitReplacement_pair(self, ctx: parmenides_tboxParser.Replacement_pairContext):
        if ctx is None:
            return tuple([None, None])
        else:
            return tuple([unfold_string(ctx.src), unfold_string(ctx.dst)])


    def visitKey_values(self, ctx: parmenides_tboxParser.Key_valuesContext):
        if ctx is None:
            return tuple([None, None])
        else:
            return tuple([unfold_string(ctx.STRING()), [self.visit(x) for x in ctx.formula()]])

    def visitValue(self, ctx: parmenides_tboxParser.ValueContext):
        return unfold_string(ctx.STRING())

    def visitNone(self, ctx: parmenides_tboxParser.NoneContext):
        return None

def parse_query(s):
    lexer = parmenides_tboxLexer(InputStream(s))
    stream = CommonTokenStream(lexer)
    parser = parmenides_tboxParser(stream)
    v = TBoxVisitor()
    return v.visit(parser.parmenides_tbox())


if __name__ == "__main__":
    input_text = ""
    with open("file.txt") as f:
        input_text = f.read()
    lexer = parmenides_tboxLexer(InputStream(input_text))
    stream = CommonTokenStream(lexer)
    parser = parmenides_tboxParser(stream)
    v = TBoxVisitor()
    obj = v.visit(parser.parmenides_tbox())
    print(obj)