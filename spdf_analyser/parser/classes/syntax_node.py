from ... import *

from .token import Token


class SyntaxNode:
    def __init__(self, value: str | Token, children: Iterable[Self]=None) -> None:
        self.value: str | Token = value
        self.children: list[Self] = list(children or [])

    def __str__(self, level: int = 0) -> str:
        text = "\t" * level + repr(self.value) + "\n"
        for child in self.children:
            text += child.__str__(level + 1)
        return text

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"

    def find_nodes(self, *args: Callable[[Self], bool]) -> List[List[Self]]:
        nodes: List[List[SyntaxNode]] = list([[] for _ in range(len(args))])
        pending = [self]
        while pending:
            # Search the tree for a object
            node = pending.pop(0)

            # Go through nodes and add them to pending
            for child in node.children:
                for i, arg in enumerate(args):
                    # If child is a wanted node
                    if arg(child):
                        nodes[i].insert(0, child)
                pending.append(child)

        return nodes

    def find_tokens(self, *args: str | Callable[[Iterable[Token]], Iterable[Token]]) -> List[List[Iterable[Token]]]:
        tokens: List[List[Iterable[Token]]] = list([[] for _ in range(len(args))])
        pending = [self]
        while pending:
            # Search the tree for a object
            node = pending.pop()

            node_tokens: List[Token] = []

            # Go through nodes and add them to pending
            for child in node.children[::-1]:
                if isinstance(child.value, Token):
                    # Token in children of each node
                    node_tokens.insert(0, child.value)
                pending.append(child)

            # Category choosen is found
            for i, arg in enumerate(args):
                if isinstance(arg, str):
                    # Match with categories if argument is a string
                    found = [node_token for node_token in node_tokens if node_token.category == arg]
                    if found:
                        tokens[i].append(found)
                elif isinstance(arg, Callable):
                    # Runs the argument with all node tokens if argument is a callable
                    found = arg(node_tokens)
                    if found:
                        tokens[i].append(found)
                else:
                    raise ValueError("Inappropriate argument given")

        return tokens

    def get_all_tokens(self) -> Tuple[Token]:
        return tuple(collapse(self.find_tokens(lambda x: x)[0]))