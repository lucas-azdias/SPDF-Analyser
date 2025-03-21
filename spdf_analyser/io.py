from . import *

ENDL = Enum("ENDL", ["CRLF", "LF", "UNKNOWN"])


def file_loader(path: Path, print_status: bool = False) -> bytes | None:
    # Try loading file
    print("Loading file...", end=" ") if print_status else ...
    try:
        with open(path, "rb") as file:
            content = file.read()
            file.close()
    except:
        print("failed.\n") if print_status else ...
        return None
    else:
        print("successfully.\n") if print_status else ...
        return content


def file_writter(path: Path, text: str, encoding: str = "utf-8", print_status: bool = False) -> bool:
    # Try writting file
    print("Writting file...", end=" ") if print_status else ...
    try:
        with open(path, "w", encoding=encoding) as file:
            file.write(text)
            file.close()
    except:
        print("failed.\n") if print_status else ...
        return False
    else:
        print("successfully.\n") if print_status else ...
        return True


def config_loader(config_path: Path, encoding: str = "utf-8", print_status: bool = False) -> Dict[str, bool] | None:
    # Try loading config file
    print("Loading config file...", end=" ") if print_status else ...
    config_content = file_loader(config_path, print_status=False)

    # Convert string to boolean
    def str_to_bool(s: str) -> Optional[bool]:
        if s.lower() == "true":
            return True
        elif s.lower() == "false":
            return False
        else:
            return None

    # Try extract options
    config = None
    if config_content:
        # Decoding
        config_text = config_content.decode(encoding=encoding)

        # Getting endl marker
        match get_endl(config_content):
            case ENDL.CRLF:
                endl_marker = "\r\n"
            case ENDL.LF:
                endl_marker = "\n"
            case _:
                endl_marker = None

        # Extracting options
        lines = config_text.split(endl_marker)
        config = {
            line.split("=")[0].lower(): str_to_bool(line.split("=")[1])
            for line in lines
            # Only process lines with "=" and with valid values
            if "=" in line and not str_to_bool(line.split("=")[1]) is None
        }

    print("successfully.\n") if config else print("failed.\n")
    return config


def calc_line_column(content: bytes, offset: int, endl: ENDL = None) -> Tuple[int, int]:
    if not endl:
        endl = get_endl(content)

    if offset > len(content):
        return (None, None)

    # Get the length of the end line marker
    endl_marker, endl_size = None, None
    match endl:
        case ENDL.CRLF:
            endl_marker = b"\r\n"
            endl_size = 2
        case ENDL.LF:
            endl_marker = b"\n"
            endl_size = 1
        case _:
            endl_marker = None
            endl_size = 0

    line, column, index = 0, 0, 0
    
    while index < offset - 1:
        if content[index:index + endl_size] == endl_marker:
            line += 1
            column = 0
            index += endl_size
        else:
            column += 1
            index += 1
    
    return line, column


def get_endl(content: bytes) -> ENDL:
    if b"\r\n" in content:
        return ENDL.CRLF
    elif b"\n" in content:
        return ENDL.LF
    else:
        return ENDL.UNKNOWN