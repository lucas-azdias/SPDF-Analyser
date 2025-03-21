from ... import *

from ...io import calc_line_column
from ...parser.classes.syntax_node import SyntaxNode

from ..language import SPDF_LANGUAGE_PATTERNS


def xref_analysis(content: bytes, syntax_tree: SyntaxNode) -> Tuple[str]:
    xref_errors: List[str] = []

    # Get all necessary nodes
    trailer_node, xref_node = syntax_tree.find_nodes(
        lambda x: x.value == "EXPR__TRAILER",
        lambda x: x.value == "EXPR__XREF"
    )
    trailer_node = trailer_node[0]
    xref_node = xref_node[0]

    # Building objects
    objects: List[Tuple[int, int]] = syntax_tree.find_tokens(
        lambda x:  (int(x[0].line), int(x[0].position)) if "KEYWORD__OBJ" in [y.category for y in x] else tuple()
    )[0]

    # Get all tokens inside the XREF node
    xref_tokens = xref_node.get_all_tokens()

    # Get the STARTXREF pointer from TRAILER node
    startxref_pointer = int(trailer_node.children[-1].value.string)

    # Verify is STARTXREF points to XREF
    if not calc_line_column(content, startxref_pointer) == (xref_tokens[0].line, xref_tokens[0].position):
        xref_errors.append("STARTXREF value doesn't point to XREF")

    # Get two values after XREF and all XREF elements
    xref_gen, xref_amount = (int(xref_tokens[1].string), int(xref_tokens[2].string))
    xref_root_elem = xref_tokens[3]
    xref_elements = xref_tokens[4:]

    # Verify XREF gen
    if not xref_gen == 0:
        xref_errors.append("XREF \"gen\" has a value different of 0")

    # Verify XREF amount of elements
    if not xref_amount == len(xref_elements) + 1:
        xref_errors.append("XREF \"amount\" doesn't correspond to the right amount of elements in XREF")
    if not xref_amount == len(objects) + 1:
        xref_errors.append("XREF \"amount\" doesn't correspond to the right amount of objects in file")

    # Verify the XREF root element
    xref_root_elem_pointer, xref_root_elem_gen = SPDF_LANGUAGE_PATTERNS["XREF_ELEMENT"].match(xref_root_elem.string).groups()
    if not int(xref_root_elem_pointer) == 0:
        xref_errors.append(f"XREF root element pointer has a value different of 0")
    if not int(xref_root_elem_gen) == 65535:
        xref_errors.append(f"XREF root element \"gen\" has a value different of 65535")


    # Verify XREF elements pointers and gens
    for i, xref_element in enumerate(xref_elements):
        xref_pointer = int(SPDF_LANGUAGE_PATTERNS["XREF_ELEMENT"].match(xref_element.string).group(1))
        # xref_gen = int(SPDF_LANGUAGE_PATTERNS["XREF_ELEMENT"].match(xref_element.string).group(2))

        if not calc_line_column(content, xref_pointer) == objects[i]:
            xref_errors.append(f"XREF element {i + 1} pointer doesn't point to its corresponding object")

    return tuple(xref_errors)