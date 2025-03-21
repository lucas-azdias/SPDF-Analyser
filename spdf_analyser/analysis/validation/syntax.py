from ... import *

from ...parser.parser import LR1Parser
from ...parser.classes.syntax_node import SyntaxNode
from ...parser.classes.token import Token

from ..language import *


def syntax_analysis(tokens: Iterable[Token]) -> SyntaxNode:
    # BOTTOM-UP APPROACH PARSING
    # parser = LR0Parser(SPDF_GRAMMAR)
    parser = LR1Parser(SPDF_GRAMMAR)
    syntax_tree = parser.parse_tokens(tokens)
    return syntax_tree