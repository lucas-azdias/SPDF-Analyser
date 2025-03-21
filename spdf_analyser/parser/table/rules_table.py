from ... import *

from .. import DEFAULT_PARSER_END_MARKER, DEFAULT_PARSER_EPSILON_MARKER, DEFAULT_PARSER_STRING_MARKER, DEFAULT_PARSER_STRING_SEP
from ..classes.production_rule import ProductionRule
from ..classes.symbol import NonTerminal, Symbol, Terminal
from ..classes.unique_list import UniqueList
from ..classes.unique_tuple import UniqueTuple

from .table import Table


class RulesTable(Table[NonTerminal, List[ProductionRule]]):
    def __init__(self, start_symbol: Optional[str] = None, end_marker: str = DEFAULT_PARSER_END_MARKER) -> None:
        super().__init__(value_type = list)

        self._array: List[ProductionRule] = list()

        self._terminals: Optional[UniqueList[Terminal]] = None
        self._nonterminals: Optional[UniqueList[NonTerminal]] = None

        self._start_symbol: NonTerminal = None
        self._aug_start_symbol: Optional[NonTerminal] = None
        if start_symbol:
            self._start_symbol = NonTerminal(start_symbol)
            self._aug_start_symbol = NonTerminal(f"{start_symbol}\'")

        self._end_symbol = Terminal(end_marker, escape_value=True)
        self._epsilon_symbol = Terminal(DEFAULT_PARSER_EPSILON_MARKER, escape_value=True)
    
    def __iter__(self) -> Generator[ProductionRule, Any, None]:
        yield from self._array

    @property
    def array(self) -> Tuple[ProductionRule]:
        return self._array

    @property
    def terminals(self) -> UniqueTuple[Terminal]:
        return UniqueTuple(self._terminals)

    @property
    def nonterminals(self) -> UniqueTuple[Terminal]:
        return UniqueTuple(self._nonterminals)

    @property
    def symbols(self) -> UniqueTuple[Symbol]:
        return UniqueTuple(self.terminals + self.nonterminals)

    @property
    def start_symbol(self) -> NonTerminal:
        return self._start_symbol

    @property
    def aug_start_symbol(self) -> NonTerminal:
        return self._aug_start_symbol

    @property
    def end_symbol(self) -> NonTerminal:
        return self._end_symbol

    @property
    def epsilon_symbol(self) -> NonTerminal:
        return self._epsilon_symbol

    def build(
            self,
            rules: Optional[Iterable[Tuple[str, str]]] = None,
            string_sep: str = DEFAULT_PARSER_STRING_SEP, 
            string_marker: str = DEFAULT_PARSER_STRING_MARKER
        ) -> None:
        rules = list(rules)

        self._terminals = UniqueList()
        self._nonterminals = UniqueList([NonTerminal(p[0]) for p in rules])

        self._start_symbol: NonTerminal = NonTerminal(self._start_symbol or next(iter(rules))[0])
        self._aug_start_symbol: NonTerminal = NonTerminal(f"{self._start_symbol}\'")

        if self._aug_start_symbol in self.symbols:
            raise ValueError("Incapable of creating augmented start symbol")

        # Convert empty RHS to epsilon marker
        for i in range(len(rules)):
            if rules[i][1] == "":
                rules[i] = (rules[i][0], DEFAULT_PARSER_EPSILON_MARKER)

        # Build production rules
        self._array = [
            ProductionRule(
                NonTerminal(RulesTable._parse_rule_side(lhs, string_marker, string_sep)[0][0]),
                tuple(
                    Terminal(x, escape_value=(not is_regex)) if not NonTerminal(x) in self._nonterminals else NonTerminal(x)
                    for x, is_regex in RulesTable._parse_rule_side(rhs, string_marker, string_sep)
                )
            )
            for lhs, rhs in rules
            if lhs and rhs # Garantee existing LHS and RHS
        ]

        # Add augmented rule
        self._array.insert(0,
            ProductionRule(
                self._aug_start_symbol,
                (self._start_symbol, )
            )
        )

        # Build table based on array
        for rule in self._array:
            self._table[rule.lhs].append(rule)

        # Identify the terminal symbols based on non-terminals
        self._terminals = UniqueList([
            symbol for production in self._array for symbol in production.rhs
            if symbol.is_terminal()
        ])

        # Add the end marker to the terminals
        if self._end_symbol in self._terminals:
            raise ValueError("End marker already in terminals")
        self._terminals.append(self._end_symbol)

    def find(self, rule: ProductionRule) -> int:
        for i, current_rule in enumerate(self.array):
            if rule == current_rule:
                return i
        return -1

    def _parse_rule_side(hs: str, marker: str, string_sep: str) -> Tuple[Tuple[str, bool]]:
        # Compile pattern to find substrings with marker
        hs_pattern_marker = (lambda m: compile(fr"{m}(.*?){m}"))(marker)

        # Find positions of all marked strings in the original HS
        marked_positions = {m.start(): m.end() for m in hs_pattern_marker.finditer(hs)}

        marker_size = len(marker)
        sep_size = len(string_sep)

        parts = []
        index = 0

        # Iterate over the string and split at string_sep while preserving marked substrings
        while index < len(hs):
            # If the current index is at the start of a marked string
            if index in marked_positions:
                # Find the end of the marked string
                end_index = marked_positions[index]
                parts.append((hs[index + marker_size:end_index - marker_size], True)) # Ignore the marker
                index = end_index + sep_size
            else:
                # Find the next separator
                next_sep = hs.find(string_sep, index)

                # If no more separators in the string, end
                if next_sep == -1:
                    parts.append((hs[index:], False))
                    break

                # Get up to the next separator
                parts.append((hs[index:next_sep], False))
                index = next_sep + sep_size

            # Remove empty strings
            if parts[-1] == "":
                parts.pop()

        # Remove epsilon in multiple symbol RHS
        if DEFAULT_PARSER_EPSILON_MARKER in (part[0] for part in parts) and len(parts) > 1:
            parts = [part for part in parts if part[0] != DEFAULT_PARSER_EPSILON_MARKER]

        return tuple(parts)