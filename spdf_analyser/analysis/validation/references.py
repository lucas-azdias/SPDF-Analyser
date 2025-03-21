from ... import *

from ...parser.classes.syntax_node import SyntaxNode
from ...parser.classes.token import Token

from ..language import SPDF_LANGUAGE_PATTERNS


def references_analysis(syntax_tree: SyntaxNode) -> Tuple[Token]:
    # Get all references tokens and all objects
    found_tokens = syntax_tree.find_tokens(
        "REFERENCE",
        lambda x:  (int(x[0].string), int(x[1].string)) if "KEYWORD__OBJ" in [y.category for y in x] else tuple() # First and second unsigned integer
    )

    references: List[Token] = list(collapse(found_tokens[0]))
    objects: List[Tuple[int, int]] = found_tokens[1]
    
    # Check references with objects
    notfound_refs = list()
    for reference in references:
        obj_id = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(reference.string).group(1)) # First unsigned integer
        obj_gen = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(reference.string).group(2)) # Second unsigned integer
        if not (obj_id, obj_gen) in objects:
            notfound_refs.append(reference)

    # Return all token references not found in objects
    return tuple(notfound_refs)