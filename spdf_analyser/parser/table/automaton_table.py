from ... import *

from ..classes.production_rule import ProductionRule
from ..classes.state import State
from ..classes.state_item import StateItem
from ..classes.transition import Transition

from .first_table import FirstTable
from .follow_table import FollowTable
from .rules_table import RulesTable
from .table import Table


class AutomatonTable(Table[int, State]):
    @property
    def states(self) -> Tuple[State]:
        return tuple(self._table.values())

    def build(self, rules_table: RulesTable, first_table: FirstTable, follow_table: FollowTable) -> None:
        # Tecnically speaking, the automaton table is a directed acyclic graph of all states with root in the augmented start production rule
        initial_state = State([StateItem(rules_table[rules_table.aug_start_symbol][0], 0, [rules_table.end_symbol])])
        initial_state.closure(rules_table, first_table)

        automaton_states: List[State] = [initial_state]
        pending_states: List[State] = [initial_state]
        visited_states: List[State] = []

        transitions: Dict[Tuple[int, ProductionRule], Transition] = dict()

        # Solve remaining states (BFS scan)
        # Stop when dot position in each branch reachs the length of the RHS
        while pending_states:
            current_state = pending_states.pop(0) # FIFO

            # For each rule, computes the next state from current state with next symbol as target
            for item in current_state:
                if item.dot_position >= len(item.production.rhs):
                    continue

                symbol = item.production.rhs[item.dot_position]

                # Handle target symbols for common symbol or epsilon case
                target_symbols = (symbol, ) if symbol != rules_table.epsilon_symbol else follow_table[item.production.lhs]

                for target_symbol in target_symbols:
                    next_state = State.goto(
                        current_state,
                        target_symbol,
                        rules_table,
                        first_table
                    )

                    index = None
                    if next_state and next_state not in visited_states:
                        # Add next state if not seen before
                        automaton_states.append(next_state)
                        pending_states.append(next_state)
                        visited_states.append(next_state)

                        # Quick index to transition
                        index = len(automaton_states) - 1
                    
                    elif next_state and next_state in visited_states:
                        # Find current state index to create transition
                        index = automaton_states.index(next_state)

                    if index:
                        # Create transition from current rule to next state
                        transitions[(automaton_states.index(current_state), item.production)] = Transition(target_symbol, index)

        # # Apply transitions to each item reference
        for (current_state, rule), transition in transitions.items():
            for item in automaton_states[current_state]:
                if item.production == rule:
                    item.transition = transition
        
        # Apply automaton states to table
        for i, state in enumerate(automaton_states):
            self._table[i] = state
    
    def find(self, state: State) -> int:
        for i, current_state in self:
            if state == current_state:
                return i
        return -1