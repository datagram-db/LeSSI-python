grammar parmenides_tbox;
// java -jar antlr-4.13.1-complete.jar  -Dlanguage=Python3 -visitor  Parmenides/TBox/parmenides_tbox.g4
parmenides_tbox: (rule ';')+;

rule: 'UPDATE' formula 'over' ontology_query ('replace' replacement_pair+)? operations* #substitutions
    | 'INVENT' 'from' formula 'as' formula 'over' ontology_query ('replace' replacement_pair+)? operations* #invention
    ;

formula: '(' formula ')'  #fparen
       | STRING '?'                                                                      #rw_variable
       | name=opt_string type=opt_string specification=opt_string cop=formula?            #variable
       | rel=opt_string '(' arg=formula ')'  score=NUMBER '{' key_values* '}'            #unary_predicate
       | rel=opt_string '(' src=formula ',' dst=formula ')' score=NUMBER '{' key_values* '}' #binary_predicate
       | 'AND' formula formula+                                                          #and
       | 'OR' formula formula+                                                           #or
       | 'NOT' formula                                                                   #not
       ;

operations: 'rem' STRING              #remove
          | 'add' formula 'to' STRING #add
          | 'with-properties'         #all_properties
          ;

ontology_query: src=STRING edge=STRING dst=STRING #edge_match
              | 'isa' src=STRING dst=STRING       #isa_match
              | 'all' '[' (ontology_query ',')* ontology_query? ']'     #all_queries
              ;

replacement_pair: src=STRING '->' dst=STRING;

key_values : STRING ':' (formula ',')* formula '.';

opt_string : STRING #value
           | NULL   #none
           ;

STRING : '"' (~[\\"] | '\\' [\\"])* '"';
NULL: 'none';
NUMBER : [-]? DecimalFloatingConstant | [-]? DIGIT;
INTEGER : [-]? DIGIT;
SPACE : [ \t\r\n]+ -> skip;
COMMENT
    : '/*' .*? '*/' -> skip
;

LINE_COMMENT
    : '#' ~[\r\n]* -> skip
;

fragment
DecimalFloatingConstant
    :   [0-9]* '.' DIGIT
        |   DIGIT '.'

    |   DIGIT ExponentPart
    ;

fragment
FractionalConstant
    :   [0-9]* '.' DIGIT
    |   DIGIT '.'
    ;

fragment
ExponentPart
    :   [eE] [-]? DIGIT
    ;

fragment DIGIT : [0-9]+;