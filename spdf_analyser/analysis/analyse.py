from .. import *

from ..io import config_loader, file_loader, file_writter
from ..parser.classes.syntax_node import SyntaxNode
from ..parser.classes.token import Token

from .language import SPDF_LANGUAGE_PATTERNS
from .validation.hierarchy import hierarchy_analysis
from .validation.lexical import lexicon_analysis, has_margins_analysis
from .validation.syntax import syntax_analysis
from .validation.references import references_analysis
from .validation.xref import xref_analysis


def analyse(path: Path, config_path: Optional[Path] = None, output_path: Path = Path("output.txt"), encoding: str="utf-8") -> None:
    # Try loading file 
    file_content = file_loader(path, print_status=True)
    if not file_content:
        return None

    # Try loading config file 
    config = config_loader(config_path, encoding=encoding, print_status=True) if config_path else None
    
    start = time_ns()

    # VALIDATION
    syntax_tree, hierarchy, types, outlines_ref, metadata_ref = validation(file_content, encoding)

    # Getting all raw data
    raw_data = get_raw_data(syntax_tree)

    # Getting metadata
    metadata_data = get_metadata_data(syntax_tree, metadata_ref)

    # STATISTICS
    statistics(file_content, syntax_tree, types, raw_data, encoding)

    # CONTENT
    content(raw_data, metadata_data)

    # OBJECTS TREE
    objects_tree(hierarchy, types)

    # ADVANCED ANALYSIS
    if config:
        outlines = get_outlines(syntax_tree, outlines_ref, hierarchy)
        advanced_analysis(config, output_path, raw_data, outlines, hierarchy, types, encoding)

    # Final message
    print(f"Executed analysis into {(time_ns() - start) / 1_000_000_000:.2}s", end="")


def validation(file_content: bytes, encoding: str="utf-8") -> Tuple[SyntaxNode, Dict[Tuple[int, int], List[Tuple[int, int]]], Dict[int, Tuple[str, str]]]:
    validation_errors: Dict[str, List[str]] = defaultdict(list)

    # Lexicon analysis
    tokens = lexicon_analysis(file_content.decode(encoding))
    for token in tokens:
        if token.category == None:
            validation_errors["General structure"].append(f"Failed when trying to classify \"{token.string}\" at the line {token.line + 1} and at the position {token.position + 1}")

    # Header and EOF analysis
    has_header, has_eof = has_margins_analysis(tokens)
    if not has_header:
        validation_errors["General structure"].append("Header not found")
    if not has_eof:
        validation_errors["General structure"].append("EOF not found")

    # Syntax analysis
    syntax_tree = None
    try:
        syntax_tree = syntax_analysis(tokens)
    except Exception as e:
        validation_errors["Objects syntax"].append(f"Error when trying to generate the syntactic tree: {str(e)}")

    # References analysis
    if syntax_tree:
        notfound_refs = references_analysis(syntax_tree)
        for notfound_ref in notfound_refs:
            validation_errors["References"].append(f"Found invalid reference \"{notfound_ref.string}\" at the line {notfound_ref.line + 1} and at the position {notfound_ref.position + 1} which doesn't point to any object")
    else:
        validation_errors["References"].append("Unable to execute the references analysis")

    # XREF analysis
    if syntax_tree:
        xref_errors = xref_analysis(file_content, syntax_tree)
        if xref_errors:
            validation_errors["XREF table"].extend(xref_errors)
    else:
        validation_errors["XREF table"].append("Unable to execute the XREF table analysis")

    # Hierarchy analysis
    if syntax_tree:
        hierarchy_errors, hierarchy, types, outlines_ref, metadata_ref = hierarchy_analysis(syntax_tree)
        if hierarchy_errors:
            validation_errors["Hierarchy structure"].extend(hierarchy_errors)
    else:
        validation_errors["Hierarchy structure"].append("Unable to execute the hierarchy analysis")

    # Summary
    summary = ""

    summary += "VALIDATION:\n"
    summary += f"[{'OK' if not validation_errors['General structure']   else 'ERROR'}] General structure\n"
    summary += f"[{'OK' if not validation_errors['Objects syntax']      else 'ERROR'}] Objects syntax\n"
    summary += f"[{'OK' if not validation_errors['References']          else 'ERROR'}] References\n"
    summary += f"[{'OK' if not validation_errors['XREF table']          else 'ERROR'}] Tabela XREF\n"
    summary += f"[{'OK' if not validation_errors['Hierarchy structure'] else 'ERROR'}] Hierarchy structure"

    if any([error for error in validation_errors.values() if error]):
        summary += "\nErrors:"
        for validation, errors in validation_errors.items():
            if errors:
                summary += f"\n    "
                summary += "\n    + ".join([validation] + errors)
    
    print(summary + "\n")

    return syntax_tree, hierarchy, types, outlines_ref, metadata_ref


def statistics(file_content: bytes, syntax_tree: SyntaxNode, types: Dict[Tuple[int, int], Tuple[str, str]], raw_data: Tuple[Tuple[int, int], str], encoding="utf-8") -> None:
    # Summary
    summary = ""

    summary += "STATISTICS:\n"
    
    if syntax_tree:
        # Building objects
        objects = None
        objects: List[Tuple[int, int]] = syntax_tree.find_tokens(
            lambda x:  (int(x[0].string), int(x[1].string)) if "KEYWORD__OBJ" in [y.category for y in x] else tuple()
        )[0]

        # Getting amount per type
        obj_types = dict(Counter([type[0].lstrip("/") for type in types.values() if type[0] != None]))

        # Calculating structural overhead
        overhead = len(bytes("".join([stream for _, stream in raw_data]), encoding=encoding))

        summary += f"Total of objects: {len(objects) + 1 if syntax_tree else 'Undefined'}\n"
        summary += f"Objects per type: {', '.join([f'{k}={v}' for k, v in obj_types.items()])}\n"
        summary += f"Total of pages: {obj_types['Page'] if 'Page' in obj_types else 0}\n"
        summary += f"Size of document: {len(file_content)} bytes\n"
        summary += f"Structural overhead: {overhead} bytes ({100 * overhead / len(file_content):.1f}%)"
    
    else:
        summary += "Unable to extract statistics due to invalid syntax tree"

    print(summary + "\n")


def content(raw_data: Tuple[Tuple[int, int], str], metadata_data: Dict[str, str]) -> None:
    # Summary
    summary = ""

    summary += "CONTENT:\n"

    if metadata_data:
        title = SPDF_LANGUAGE_PATTERNS["LITERAL__STRING"].match(metadata_data["Title"]).group(1) if "Title" in metadata_data else ""
        author = SPDF_LANGUAGE_PATTERNS["LITERAL__STRING"].match(metadata_data["Author"]).group(1) if "Author" in metadata_data else ""
        creation_date = SPDF_LANGUAGE_PATTERNS["LITERAL__STRING"].match(metadata_data["CreationDate"]).group(1) if "Author" in metadata_data else ""

        summary += f"Title: {title}\n"
        summary += f"Author: {author}\n"
        summary += f"Creation date: {datetime.strptime(creation_date, "D:%Y%m%d%H%M%S").strftime("%d/%m/%Y %H:%M")}\n"
    else:
        summary += "Unable to extract metadata\n"
    
    if raw_data:
        summary += f"Extracted text (first 200 characters): \"{('\n'.join([stream for _, stream in raw_data]))[:200]}\""
    else:
        summary += "Unable to extract content"

    print(summary + "\n")


def objects_tree(hierarchy: Dict[Tuple[int, int], List[Tuple[int, int]]], types: Dict[int, Tuple[str, str]]) -> None:
    # Summary
    summary = ""

    summary += "OBJECTS TREE:\n"

    if hierarchy and types:
        # Finding root nodes
        is_child = {}
        for children in hierarchy.values():
            for child in children:
                is_child[child] = True
        root_nodes = [node for node in hierarchy if node not in is_child]

        def format_tree(hierarchy: Dict[Tuple[int, int], List[Tuple[int, int]]], types: Dict[int, Tuple[str, str]], node: Tuple[int, int], level: int = 0) -> List[str]:
            node_type = types.get(node, [None, None])
            node_string = f"{('   ' * (level - 1) + '+--') if level > 0 else ''}{node[0]}: {node_type[0].lstrip('/') if node_type[0] else 'Unknown'}{f' {node_type[1].lstrip('/')}' if node_type[1] else ''}"
            children = hierarchy.get(node, [])

            result = [node_string]
            for i, child in enumerate(children):
                result.extend(format_tree(hierarchy, types, child, level + 1))

            return result

        objects_tree = "\n".join(list(collapse(format_tree(hierarchy, types, root) for root in root_nodes)))

        summary += objects_tree

    else:
        summary += "Unable to extract objects tree"

    print(summary + "\n")


def advanced_analysis(config: Dict[str, bool], output_path: Path, raw_data: Tuple[Tuple[int, int], str], outlines: Tuple[Tuple[str, Tuple[int, int]]], hierarchy: Dict[Tuple[int, int], List[Tuple[int, int]]], types: Dict[int, Tuple[str, str]], encoding: str = "utf-8") -> None:
    # Summary
    summary = ""

    summary += "ADVANCED ANALYSIS:\n"

    analysis = []
    if config:
        if not any(config.values()):
            summary += "No advanced analysis set on configuration file"

        # SUMMARY
        if "generate_summary" in config and config["generate_summary"] == True:
            text = "Summary: "
            if outlines:
                text += ", ".join([SPDF_LANGUAGE_PATTERNS["LITERAL__STRING"].match(outline[0]).group(1) for outline in outlines])
            else:
                text += "Unable to generate a summary"
            analysis.append(text)

        # EXTRACT TEXT
        if "extract_text" in config and config["extract_text"] == True:
            text = "Extract text: "
            if output_path and raw_data and outlines and hierarchy:
                text_data = []
                added_texts = []
                for outline in outlines:
                    for (obj_id, obj_gen), stream in raw_data:
                        if (obj_id, obj_gen) in hierarchy[outline[1]] and not (obj_id, obj_gen) in added_texts:
                            text_data.append(format_stream(stream))
                            added_texts.append((obj_id, obj_gen))
                is_written = file_writter(output_path, "\n\n".join(text_data), encoding=encoding, print_status=False)
                text += f"{f'Exported to file \"{str(output_path)}\" with success' if is_written else 'Failed to export to file'}"
            else:
                text += "Unable to extract text"
            analysis.append(text)

        # DETECT CYCLES
        if "detect_cycles" in config and config["detect_cycles"] == True:
            text = "Detect cycles: "
            if hierarchy:
                page_hierarchy = {}
                for k, v in hierarchy.items():
                    if types[k][0] and types[k][0].lstrip("/") in ["Catalog", "Pages", "Page"]:
                        page_hierarchy[k] = [e for e in v if types[e][0] and types[e][0].lstrip("/") in ["Catalog", "Pages", "Page"]]
                text += f"{'Cycles detected' if has_cycle(page_hierarchy) else 'No cycles detected'}"
            else:
                text += "Unable to detect cycles"
            analysis.append(text)
    
    else:
        analysis.append("Unable to execute any advanced analysis")
    
    summary += "\n".join(analysis)
    
    print(summary + "\n")


def get_raw_data(syntax_tree: SyntaxNode) -> Tuple[Tuple[int, int], str]:
    raw_data = list()

    # Building objects 
    object_nodes = syntax_tree.find_nodes(
        lambda x: x.value == "EXPR__OBJ"
    )
    object_nodes = list(collapse(object_nodes))

    # Adding STREAM_BLOCK raw data
    for object_node in object_nodes:
        stream_node = object_node.find_nodes(
            lambda x: isinstance(x.value, Token) and x.value.category == "STREAM_BLOCK"
        )[0]

        if not stream_node:
            continue

        obj_id = int(object_node.children[0].value.string) # First unsigned integer
        obj_gen = int(object_node.children[1].value.string) # Second unsigned integer

        stream = SPDF_LANGUAGE_PATTERNS["STREAM_BLOCK"].match(stream_node[0].value.string).group(1)
        raw_data.append(((obj_id, obj_gen), stream))
    
    # Returning all raw data
    return raw_data


def get_outlines(syntax_tree: SyntaxNode, outlines_ref: str, hierarchy: Dict[Tuple[int, int], List[Tuple[int, int]]]) -> Optional[Tuple[Tuple[str, Tuple[int, int]]]]:
    if syntax_tree and outlines_ref:
        outlines_id = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(outlines_ref).group(1)) # First unsigned integer
        outlines_gen = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(outlines_ref).group(2)) # Second unsigned integer
        
        outlines_childs = hierarchy[(outlines_id, outlines_gen)]

        # Building objects 
        object_nodes = syntax_tree.find_nodes(
            lambda x: x.value == "EXPR__OBJ"
        )
        object_nodes = list(collapse(object_nodes))

        # Finding outlines childs nodes
        outlines_nodes = []
        for object_node in object_nodes:
            for outlines_child in outlines_childs:
                if int(object_node.children[0].value.string) == outlines_child[0] and int(object_node.children[1].value.string) == outlines_child[1]:
                    outlines_nodes.append(object_node)
        
        # Getting title from childs nodes
        titles = []
        for outlines_node in outlines_nodes:
            dict_pairs = outlines_node.find_nodes(
                lambda x: x.value == "STRUCT__DICT_PAIR"
            )[0]
            values = []
            for dict_pair in dict_pairs:
                k, v = dict_pair.children[0].value, dict_pair.children[1].children[0]
                if k.string == "/Title":
                    values.append(v.value.string)
                elif k.string == "/Dest":
                    ref = v.find_tokens("REFERENCE")[0][0][0].string
                    ref_id = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(ref).group(1)) # First unsigned integer
                    ref_gen = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(ref).group(2)) # Second unsigned integer
                    values.append((ref_id, ref_gen))
            if values:
                titles.append(tuple(values))

        return tuple(titles)
    else:
        return None


def get_metadata_data(syntax_tree: SyntaxNode, metadata_ref: str) -> Dict[str, str]:
    if not syntax_tree:
        return dict()

    # Extracting metadata
    metadata_id = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(metadata_ref).group(1)) # First unsigned integer
    metadata_gen = int(SPDF_LANGUAGE_PATTERNS["REFERENCE"].match(metadata_ref).group(2)) # Second unsigned integer

    metadata_node = None
    for node in syntax_tree.find_nodes(
        lambda x: x.value == "EXPR__OBJ"
    )[0]:
        if int(node.children[0].value.string) == metadata_id and int(node.children[1].value.string) == metadata_gen:
            metadata_node = node
    
    metadata_data = dict()
    for dict_pair in metadata_node.find_nodes(
        lambda x: x.value == "STRUCT__DICT_PAIR"
    )[0]:
        k, v = dict_pair.children[0].value, dict_pair.children[1].children[0].value
        metadata_data[k.string.lstrip("/")] = v.string
    
    return metadata_data


def format_stream(stream: str) -> Optional[str]:
    # Split the text into lines
    lines = stream.strip().split('\n')
    
    # Extract text content between parentheses
    table_lines = []
    for line in lines:
        line = line.strip()
        if line.endswith('Tj'):  # Look for text show operator
            start = line.find('(')
            end = line.find(')')
            if start != -1 and end != -1:
                text = line[start + 1:end]
                table_lines.append(text)
    
    if not table_lines:
        return None
    
    # Parse content into rows
    table_data = []
    headers = None
    
    for line in table_lines:
        # Try common separators: comma, colon, semicolon
        for separator in [', ', ': ', '; ']:
            if separator in line:
                columns = [col.strip() for col in line.split(separator)]
                table_data.append(columns)
                break
        else:
            # Single column row (like title or summary)
            table_data.append([line])
    
    # If first row seems like a header (short, no numbers), use it as headers
    first_row = table_data[0]
    if (len(first_row) > 1 and 
        not any(any(char.isdigit() for char in col) for col in first_row)):
        headers = first_row
        table_data = table_data[1:]
    
    # Use tabulate to format the table
    if not headers:
        return tabulate(table_data, tablefmt="grid")
    return tabulate(table_data, headers=headers, tablefmt="grid")


def has_cycle(graph: Dict[Any, Iterable[Any]]) -> bool:
    # Track visited nodes
    visited = {}
    
    # Check each node in case graph is disconnected
    for start_node in graph:
        if start_node in visited:
            continue
            
        # Stack for iterative DFS: (node, neighbor_index)
        stack = [(start_node, 0)]
        # Track nodes in current path for cycle detection
        path = []  # similar to recursion stack
        
        while stack:
            node, neighbor_idx = stack[-1]
            
            # If this is first visit to node
            if node not in visited:
                visited[node] = True
                path.append(node)
            
            # Get neighbors, handle case where node isn't a key
            neighbors = graph.get(node, [])
            
            # Move to next unvisited neighbor or backtrack
            while neighbor_idx < len(neighbors):
                next_node = neighbors[neighbor_idx]
                stack[-1] = (node, neighbor_idx + 1) # Update index
                
                if next_node in path:
                    return True
                if next_node not in visited:
                    stack.append((next_node, 0))
                    break
                neighbor_idx += 1
            else:
                # No more neighbors to visit, backtrack
                stack.pop()
                path.pop()
    
    return False