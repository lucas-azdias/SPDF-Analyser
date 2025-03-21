from .. import *

from . import DEFAULT_PARSER_END_MARKER, DEFAULT_PARSER_STRING_SEP, DEFAULT_PARSER_STRING_MARKER
from .classes.action_entry import PARSER_ACTION
from .classes.syntax_node import SyntaxNode
from .classes.token import Token
from .table.automaton_table import AutomatonTable
from .table.action_table import ActionTable
from .table.first_table import FirstTable
from .table.follow_table import FollowTable
from .table.rules_table import RulesTable


class LR1Parser:
    def __init__(
            self,
            productions_rules: Iterable[Tuple[str, str]],
            start_symbol: Optional[str] = None,
            string_sep: str = DEFAULT_PARSER_STRING_SEP,
            string_marker: str = DEFAULT_PARSER_STRING_MARKER,
            end_marker: str = DEFAULT_PARSER_END_MARKER
        ) -> None:
        self.apply(
            productions_rules=productions_rules,
            start_symbol=start_symbol,
            string_sep=string_sep,
            string_marker=string_marker,
            end_marker=end_marker
        )

    # --GETTERS------

    # ---------------

    # --SETTERS------

    # ---------------
    
    def apply(
            self,
            productions_rules: Iterable[Tuple[str, str]],
            start_symbol: Optional[str] = None,
            string_sep: str = DEFAULT_PARSER_STRING_SEP,
            string_marker: str = DEFAULT_PARSER_STRING_MARKER,
            end_marker: str = DEFAULT_PARSER_END_MARKER
        ) -> None:
        self._string_sep: str = string_sep

        self._rules_table: RulesTable = RulesTable(start_symbol, end_marker)
        self._first_table: FirstTable = FirstTable()
        self._follow_table: FollowTable = FollowTable()
        self._automaton_table: AutomatonTable = AutomatonTable()
        self._action_table: ActionTable = ActionTable()

        # Build production rules table
        self._rules_table.build(productions_rules, string_sep, string_marker)
        # print("PRODUCTION RULES", self._rules_table.array)

        # Build parser tables
        self.build()
    
    def build(self) -> None:
        # Build all tables

        # Build FIRST TABLE
        self._first_table.build(self._rules_table)
        # print("FIRST TABLE", self._first_table)

        # Build FOLLOW TABLE
        self._follow_table.build(self._rules_table, self._first_table)
        # print("FOLLOW TABLE", self._follow_table)

        # Build AUTOMATON STATES
        self._automaton_table.build(self._rules_table, self._first_table, self._follow_table)
        # print("STATES")
        # for i, state in enumerate(self._automaton_table):
        #     print(f"\t {i} {state}")

        # Build ACTION TABLE
        self._action_table.build(self._rules_table, self._automaton_table)
        # print("ACTION TABLE")
        # for (i, symbol), entry in self._action_table:
        #     print(f"({i}, {symbol}) {entry.action} {entry.param}")

    def parse_string(self, string: str, string_sep: Optional[str] = None) -> bool:
        stack = [0] # Initial stack with states index
        string_symbols = string.split(string_sep) + [self._rules_table.end_symbol.value] # Add end marker
        pos = 0

        while True:
            state_index = stack[-1] # Last state index
            string_symbol = string_symbols[pos] # Current symbol

            # Verify match with any state index and symbol
            symbol = None
            for (current_index, current_symbol), _ in self._action_table:
                if state_index == current_index and current_symbol.pattern.fullmatch(string_symbol):
                    symbol = current_symbol
                    break

            # Identify invalid symbol
            if symbol is None:
                return False

            # Map the current state and symbol
            entry = self._action_table[(state_index, symbol)]

            match entry.action:
                case PARSER_ACTION.SHIFT:
                    # Push the new state
                    stack.append(entry.param)
                    pos += 1

                case PARSER_ACTION.GOTO:
                    return False

                case PARSER_ACTION.REDUCE:
                    # Get the production rule
                    rule = self._rules_table.array[entry.param]

                    # Reduce by the RHS elements
                    rhs_length = len(rule.rhs) - rule.rhs.count(self._rules_table.epsilon_symbol) # Ignore epsilon elements (consider size as null)
                    if rhs_length > 0:
                        # Remove the length of RHS from the stack
                        del stack[-rhs_length:]

                    if not stack:
                        return False

                    if not (stack[-1], rule.lhs) in self._action_table.table.keys():
                        return False

                    # Get next state
                    goto_entry = self._action_table[(stack[-1], rule.lhs)]

                    # No next state found
                    if goto_entry.action != PARSER_ACTION.GOTO or not goto_entry.param:
                        return False
                    
                    # Push the new state
                    stack.append(goto_entry.param)

                case PARSER_ACTION.ACCEPT:
                    # Sentence accepted
                    return True

                case PARSER_ACTION.ERROR:
                    # TODO
                    ...

                case PARSER_ACTION.CONFLICT:
                    # TODO
                    ...

    def parse_tokens(self, tokens: Iterable[Token]) -> SyntaxNode:
        stack = [(0, None)] # Initial stack with states index
        tokens = (*tokens, Token(self._rules_table.end_symbol.value, self._rules_table.end_symbol.value, None, None)) # Add end marker
        pos = 0

        while True:
            state_index = stack[-1][0] # Last state index
            token = tokens[pos] # Current symbol

            # Verify match with any state index and symbol
            symbol = None
            for (current_index, current_symbol), _ in self._action_table:
                if state_index == current_index and current_symbol.pattern.fullmatch(token.category):
                    symbol = current_symbol
                    break

            # Identify invalid symbol
            if symbol is None:
                raise ValueError(f"Invalid symbol \"{token.category}\" at state {state_index}")

            # Map the current state and symbol
            entry = self._action_table[(state_index, symbol)]

            match entry.action:
                case PARSER_ACTION.SHIFT:
                    # Create a terminal node and push it with the new state
                    node = SyntaxNode(token)
                    stack.append((entry.param, node))
                    pos += 1

                case PARSER_ACTION.GOTO:
                    raise ValueError("Unexpected GOTO on token input")

                case PARSER_ACTION.REDUCE:
                    # Get the production rule
                    rule = self._rules_table.array[entry.param]

                    # Reduce by the RHS elements
                    rhs_length = len(rule.rhs) - rule.rhs.count(self._rules_table.epsilon_symbol) # Ignore epsilon elements (consider size as null)
                    if rhs_length > 0:
                        # Remove the length of RHS from the stack
                        # del stack[-rhs_length:]
                        rhs_nodes = [stack.pop()[1] for _ in range(rhs_length)]
                        rhs_nodes.reverse() # Preserve order (left-to-right)
                    else:
                        rhs_nodes = []  # Epsilon production

                    # Create a new node for the LHS non-terminal
                    new_node = SyntaxNode(rule.lhs.value, children=rhs_nodes)

                    if not stack:
                        raise ValueError(f"Empty stack after REDUCE")

                    if not (stack[-1][0], rule.lhs) in self._action_table.table.keys():
                        raise ValueError(f"Invalid pair (\"{stack[-1][0]}\", \"{rule.lhs}\") in ACTION table")

                    # Get next state
                    goto_entry = self._action_table[(stack[-1][0], rule.lhs)]

                    # No next state found
                    if goto_entry.action != PARSER_ACTION.GOTO or not goto_entry.param:
                        raise ValueError(f"Invalid GOTO state for \"{rule.lhs}\"")
                    
                    # Push the new state and node
                    stack.append((goto_entry.param, new_node))

                case PARSER_ACTION.ACCEPT:
                    # Sentence accepted
                    if len(stack) < 2:
                        raise ValueError("Stack too small on ACCEPT")
                    root_node = stack[-1][1]  # The node for START
                    return root_node

                case PARSER_ACTION.ERROR:
                    # TODO
                    ...

                case PARSER_ACTION.CONFLICT:
                    # TODO
                    ...


# Example usage
if __name__ == "__main__":
    grammar1 = [
        ("E", "E + B"),
        ("E", "B"),
        ("B", "0"),
        ("B", "1"),
    ]
    grammar2 = [
        ("S", "A a"),
        ("A", "b"),
        ("A", "ε"),
    ]

    parser1 = LR1Parser(grammar1)
    parser2 = LR1Parser(grammar2)

    print(parser1.parse_string("1 + 0 + 1"))  # True
    print(parser2.parse_string("b a"))  # True