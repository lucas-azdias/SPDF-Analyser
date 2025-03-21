from ... import *

from ..classes.symbol import NonTerminal, Terminal
from ..classes.unique_list import UniqueList

from .first_table import FirstTable
from .rules_table import RulesTable
from .table import Table


class FollowTable(Table[NonTerminal, UniqueList[Terminal]]):
    def __init__(self) -> None:
        super().__init__(value_type = UniqueList)

    def build(self, rules_table: RulesTable, first_table: FirstTable) -> None:
        self.from_keys([k for k in rules_table.table.keys() if k.is_non_terminal()])

        # Default follow value for the starting symbol
        self._table[rules_table.aug_start_symbol].append(rules_table.end_symbol)

        has_changed = True
        while has_changed:
            has_changed = False

            # Build the first table
            for rule in rules_table:
                # For each symbol in the RHS
                for i in range(len(rule.rhs)):
                    symbol = rule.rhs[i]

                    if not symbol.is_non_terminal():
                        continue

                    next_symbol = rule.rhs[i + 1] if i + 1 < len(rule.rhs) else None

                    old_len = len(self._table[symbol])

                    if next_symbol and next_symbol.is_terminal() and next_symbol != rules_table.epsilon_symbol:
                        # Add following terminal
                        self._table[symbol].append(next_symbol)
                
                    elif next_symbol and next_symbol.is_non_terminal():
                        # Add result of first table for following non-terminal
                        self._table[symbol].extend(first_table[next_symbol] - {rules_table.epsilon_symbol})
                        if rules_table.epsilon_symbol in first_table[next_symbol]:
                            self._table[symbol].extend(self._table[rule.lhs])

                    elif i == len(rule.rhs) - 1 or next_symbol == rules_table.epsilon_symbol:
                        # Add result of follow table for last and empty followed symbol
                        self._table[symbol].extend(self._table[rule.lhs])
                    
                    else:
                        raise Exception("Non-Symbol value found")

                    # Check if there was any change
                    if old_len < len(self._table[symbol]):
                        has_changed = True