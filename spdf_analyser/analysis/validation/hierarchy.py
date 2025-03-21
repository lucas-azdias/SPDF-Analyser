from ... import *

from ...parser.classes.syntax_node import SyntaxNode

from ..language import SPDF_LANGUAGE_PATTERNS


def hierarchy_analysis(syntax_tree: SyntaxNode) -> Tuple[Tuple[str], Dict[Tuple[int, int], List[Tuple[int, int]]], Dict[Tuple[int, int], Tuple[str, str]], str, str]:
    hierarchy_errors = []

    # Get the dict pairs nodes from trailer node
    dict_nodes = syntax_tree.find_nodes(
        lambda x: x.value == "EXPR__TRAILER"
    )[0][0].find_nodes(
        lambda x: x.value == "STRUCT__DICT_PAIR"
    )[0]

    # Getting root node
    root_node_ref = None
    for dict_node in dict_nodes:
        tokens = dict_node.get_all_tokens()
        if tokens[0].string == "/Root":
            root_node_ref = tokens[1].string

    # Failed to get root node reference
    if not root_node_ref:
        hierarchy_errors.append("Failed to get root node reference")
        return hierarchy_errors, None, None

    # Building objects
    objects_refs = syntax_tree.find_tokens(
        lambda x: (int(x[0].string), int(x[1].string)) if "KEYWORD__OBJ" in [y.category for y in x] else tuple()
    )[0]
    object_nodes = syntax_tree.find_nodes(
        lambda x: x.value == "EXPR__OBJ"
    )
    object_nodes = list(collapse(object_nodes))

    # Verifing hierarchy
    hierarchy: Dict[int, List[int]] = defaultdict(list) # Map from obj_id to children obj_ids
    types: Dict[int, (str, str)] = dict() # Map obj_id to object type and subtype

    expected_types = ["/Catalog", "/Pages", "/Page", "(^/Font$)|(^/Contents$)", "/FontDescriptor"]
    outlines_type = "/Outlines"
    metadata_type = "/Metadata"
    pending = [(root_node_ref, None, None, 0)] # Tuple with next node reference, previous node reference, parent reference and expected type for next one
    outlines_ref = None
    metadata_ref = None
    while pending:
        obj, prev, parent, exp_index_type = pending.pop() # FIFO
        obj_id = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(obj).group(1)) # First unsigned integer
        obj_gen = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(obj).group(2)) # Second unsigned integer

        # Get the current object node via reference
        index = objects_refs.index((obj_id, obj_gen))
        references = [r.string for r in collapse(object_nodes[index].find_tokens("REFERENCE"))]
        dict_pairs = object_nodes[index].find_nodes(
            lambda x: x.value == "STRUCT__DICT_PAIR"
        )[0]

        # Search for the info inside the node
        type_ref = None
        subtype_ref = None
        next_ref = None
        prev_ref = None
        for dict_pair in dict_pairs:
            k, v = dict_pair.children[0].value, dict_pair.children[1].children[0].value
            match k.string:
                case "/Type":
                    type_ref = v.string
                case "/Subtype":
                    subtype_ref = v.string
                case "/Next":
                    next_ref = v.string
                    references.remove(next_ref)
                case "/Prev":
                    prev_ref = v.string
                    references.remove(prev_ref)
                case "/Parent":
                    references.remove(v.string)
                case "/Dest":
                    refs = collapse(dict_pair.find_tokens("REFERENCE"))
                    for ref in refs:
                        references.remove(ref.string)
                case "/Last":
                    references.remove(v.string)
                case "/Outlines":
                    if not outlines_ref:
                        outlines_ref = v.string
                        references.remove(outlines_ref)
                        pending.append((outlines_ref, None, None, None))
                    else:
                        hierarchy_errors.append(f"Object {obj} tried to overwrite the outlines")
                case "/Metadata":
                    if not metadata_ref:
                        metadata_ref = v.string
                        references.remove(metadata_ref)
                        pending.append((metadata_ref, None, None, None))
                    else:
                        hierarchy_errors.append(f"Object {obj} tried to overwrite the metadata")

        if exp_index_type and match(expected_types[exp_index_type], "/Content"):
            type_ref = "/Content"
        elif exp_index_type and match(expected_types[exp_index_type], "/Font"):
            type_ref = "/Font"
        
        if not exp_index_type is None and not type_ref and obj != metadata_ref and obj != metadata_ref and type_ref != "/Contents" and type_ref != "/Font":
            hierarchy_errors.append(f"Object \"{obj}\" has no defined type, expected \"{expected_types[exp_index_type]}\"")

        elif obj == outlines_ref:
            type_ref = outlines_type

        elif obj == metadata_ref:
            type_ref = metadata_type

        elif not exp_index_type is None:
            type_index = None
            for i, expected_type in enumerate(expected_types):
                if match(expected_type, type_ref):
                    type_index = i
                    break

            if type_index is None or type_index != exp_index_type:
                hierarchy_errors.append(f"Object \"{obj}\" has a type \"{type_ref}\", expected \"{expected_types[exp_index_type]}\"")

        if next_ref:
            pending.append((next_ref, obj, parent, exp_index_type))

        if prev_ref != prev:
            hierarchy_errors.append(f"Object \"{obj}\" has a previous object \"{prev_ref}\", expected \"{prev}\"")

        if parent:
            parent_id = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(parent).group(1)) # First unsigned integer
            parent_gen = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(parent).group(2)) # Second unsigned integer
            if not (obj_id, obj_gen) in hierarchy[(parent_id, parent_gen)]:
                hierarchy[(parent_id, parent_gen)].append((obj_id, obj_gen))

        if not exp_index_type is None:
            for reference in references:
                pending.append((reference, None, obj, exp_index_type + 1))
        else:
            for reference in references:
                pending.append((reference, None, obj, None))

        types[(obj_id, obj_gen)] = type_ref, subtype_ref
        
        if not pending:
            for id, gen in objects_refs:
                if not (id, gen) in types.keys():
                    pending.append((f"{id} {gen} R", None, None, None))

    return hierarchy_errors, hierarchy, types, outlines_ref, metadata_ref