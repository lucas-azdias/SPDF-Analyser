from ... import *

from ..classes.production_rule import ProductionRule
from ..classes.symbol import NonTerminal, Terminal
from ..classes.unique_list import UniqueList

from .rules_table import RulesTable
from .table import Table


class FirstTable(Table[NonTerminal, UniqueList[Terminal]]):
    def __init__(self) -> None:
        super().__init__(value_type = UniqueList)

    def build(self, rules_table: RulesTable) -> None:
        self.from_keys([k for k in rules_table.table.keys() if k.is_non_terminal()])

        has_changed = True
        while has_changed:
            has_changed = False

            # Build the first table
            for rule in rules_table:
                old_len = len(self._table[rule.lhs])

                # Empty RHS case
                if rule.is_rhs_empty():
                    self._table[rule.lhs].append(rules_table.epsilon_symbol)
                
                # For each symbol in the RHS
                for symbol in rule.rhs:
                    if symbol.is_terminal():
                        # Add first terminal
                        self._table[rule.lhs].append(symbol)
                        break
                
                    elif symbol.is_non_terminal():
                        # Add result of first table for non-terminal
                        self._table[rule.lhs].extend(self._table[symbol] - [rules_table.epsilon_symbol])
                        if not ProductionRule(symbol, (rules_table.epsilon_symbol, )) in rules_table[symbol]:
                            break

                    else:
                        # If not broken manually
                        self._table[rule.lhs].append(rules_table.epsilon_symbol)

                # Check if there was any change
                if old_len < len(self._table[rule.lhs]):
                    has_changed = True