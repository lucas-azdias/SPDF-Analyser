from ... import *

from ..classes.action_entry import ActionEntry, PARSER_ACTION
from ..classes.symbol import Symbol

from .automaton_table import AutomatonTable
from .rules_table import RulesTable
from .table import Table


class ActionTable(Table[Tuple[int, Symbol], ActionEntry]):
    def build(self, rules_table: RulesTable, automaton_table: AutomatonTable) -> None:
        # Build the action table for the automate parser based on the states items transitions and end items (when dot position is at the end)
        # The action table maps from a current state with a symbol to an action and a parameter
        for i, state in automaton_table:
            # Build table entries for each item in the state
            for item in state:
                if item.transition and item.transition.from_symbol.is_terminal():
                    # Insert SHIFT action
                    index = item.transition.to_state
                    self._table[(i, item.transition.from_symbol)] = ActionEntry(PARSER_ACTION.SHIFT, index)

                elif item.transition and item.transition.from_symbol.is_non_terminal():
                    # Insert GOTO action
                    index = item.transition.to_state
                    self._table[(i, item.transition.from_symbol)] = ActionEntry(PARSER_ACTION.GOTO, index)

                elif (item.dot_position == len(item.production.rhs) or item.production.rhs[item.dot_position] == rules_table.epsilon_symbol) and item.production.lhs != rules_table.aug_start_symbol:
                    # Insert REDUCE action
                    index = rules_table.find(item.production)
                    for lookahead in item.lookaheads:
                        self._table[(i, lookahead)] = ActionEntry(PARSER_ACTION.REDUCE, index)

                elif item.dot_position == len(item.production.rhs) and item.production.lhs == rules_table.aug_start_symbol:
                    # Insert ACCEPT action
                    self._table[(i, rules_table.end_symbol)] = ActionEntry(PARSER_ACTION.ACCEPT, None)

                # elif something:
                #     # TODO
                #     # Insert ERROR action

                # elif something:
                #     # TODO
                #     # Insert CONFLICT action

                else:
                    pass
                    # raise Exception("Exception when building ACTION table")