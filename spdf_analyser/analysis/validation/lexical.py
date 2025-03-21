from ... import *

from ...parser.parser import *
from ...parser.classes.token import *

from ..language import *


def lexicon_analysis(content: str) -> Tuple[Token]:
    # Combine tokens patterns into one regex
    tokens_regex = compile("|".join(f"(?P<{cat}>{pat.pattern})" for cat, pat in SPDF_LANGUAGE_PATTERNS.items()))
    
    # Split content into lines (except for stream blocks)
    stream_blocks: List[Match[str]] = [x for x in finditer(SPDF_LANGUAGE_PATTERNS["STREAM_BLOCK"], content)] # All stream block matches in the content
    current_block: int = 0 # Index to track which stream block is being processed
    lines: List[List[int, str]] = [[0, ""]] # List to store lines of content
    pos: int = 0 # Current position in the content
    jump_lines: int = 1 # How many lines add to counter when adding new line
    while pos < len(content):
        # If a stream block starts at the current position, append it as is
        if stream_blocks and current_block < len(stream_blocks) and stream_blocks[current_block].start() <= pos:
            matched_string = content[pos:stream_blocks[current_block].end()]
            lines[-1][1] += matched_string # Add entire stream block
            pos = stream_blocks[current_block].end()
            jump_lines += matched_string.count("\n")
            current_block += 1 # Next stream block
            continue

        # Newline found
        elif content[pos] == "\n":
            lines.append([lines[-1][0] + jump_lines, ""])
            pos += 1
            jump_lines = 1
            continue

        # Otherwise, add the character to the current line
        lines[-1][1] += content[pos]
        pos += 1
    
    tokens = [] # Tokens already validated
    
    # Process each line
    for i, line in lines:
        pos = 0 # Current start match position in line (i.e. column)
        
        while pos < len(line):
            # Skip whitespace
            if line[pos].isspace():
                pos += 1
                continue
                
            # Try to match a token at current position
            match = tokens_regex.match(line, pos)

            if not match or not pos == match.start():
                # If no match found or start position is not the same, undefined lexicon found
                end_lexicon = line[pos:].find(" ")
                if end_lexicon < 0:
                    end_lexicon = len(line)
                else:
                    end_lexicon += pos
                tokens.append(Token(None, line[pos:end_lexicon], i, pos))
                pos = end_lexicon
                continue

            # Get the matched token and its category
            for cat in [k for k, _ in SPDF_LANGUAGE_PATTERNS.items()]:  # Respect priority order
                token = match.group(cat)
                if token is not None:
                    tokens.append(Token(cat, token, i, pos))
                    pos = match.end()
                    break

    return tuple(tokens)


def has_margins_analysis(tokens: Iterable[Token]) -> Tuple[bool, bool]:
    if not tokens:
        return False, False

    first_line = tokens[0].line
    last_line = tokens[-1].line
    first_count = 0
    last_count = 0

    # Count tokens in the first valid line
    for token in tokens:
        if token.line != first_line:
            break
        first_count += 1

    # Count tokens in the last valid line
    for token in tokens[::-1]:
        if token.line != last_line:
            break
        last_count += 1

    # Header in first position in first valid line
    has_header = first_count == 1 and tokens[0].category == "MARGIN__HEADER"

    # EOF in first position in last valid line
    has_eof = last_count == 1 and tokens[-1].category == "MARGIN__EOF"
    
    return has_header, has_eof