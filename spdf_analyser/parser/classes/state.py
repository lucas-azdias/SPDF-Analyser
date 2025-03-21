from ... import *

from ..table.first_table import FirstTable
from ..table.follow_table import FollowTable
from ..table.rules_table import RulesTable

from .state_item import StateItem
from .unique_list import UniqueList
from .unique_tuple import UniqueTuple


class State:
    __slots__ = ("items")

    def __init__(self, items: Iterable[StateItem]) -> None:
        self.items: UniqueTuple[StateItem] = UniqueTuple(items)

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, State) and 
                self.items == other.items)

    def __hash__(self) -> int:
        return hash(self.items)

    def __str__(self) -> str:
        return f"{", ".join(map(str, self.items))}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"

    def __iter__(self) -> Generator[StateItem, Any, None]:
        yield from self.items

    def __bool__(self) -> bool:
        return len(self.items) > 0

    def closure(self, rules_table: RulesTable, first_table: FirstTable) -> None:
        # Calculate the closure of the state by adding expanded production rules
        # I.e. expand the state by adding all productions of non-terminals that appear immediately after a dot
        closure_list = list(self.items)

        # Keep adding production rules based on the non-terminals in each RHS (while closure list keeps changing)
        has_changed = True
        while has_changed:
            new_items: UniqueList[StateItem] = UniqueList()

            # For all state items
            for item in closure_list:
                # Skip if dot is at end of RHS
                if item.dot_position >= len(item.production.rhs):
                    continue

                next_symbol = item.production.rhs[item.dot_position]

                # Skip if next symbol is not a non terminal
                if not next_symbol in rules_table.nonterminals:
                    continue

                # Compute the lookaheads for the new item
                if item.dot_position == len(item.production.rhs) - 1:
                    # S -> ... . E, l <==> Terminals in l can follow E
                    lookaheads = UniqueList(item.lookaheads)

                elif item.production.rhs[item.dot_position + 1].is_terminal():
                    # S -> ... . E '+', l <==> '+' can follow E
                    lookaheads = UniqueList([item.production.rhs[item.dot_position + 1]])

                elif item.production.rhs[item.dot_position + 1].is_non_terminal():
                    # S -> ... . E F, l <==> Terminals in FIRST(F, l) can follow E
                    lookaheads = UniqueList(first_table[item.production.rhs[item.dot_position + 1]])
                    if not lookaheads:
                        lookaheads.extend(item.lookaheads)

                    # If lookahead has epsilon, inherit from current item
                    elif rules_table.epsilon_symbol in lookaheads:
                        lookaheads.remove(rules_table.epsilon_symbol)
                        lookaheads.extend(item.lookaheads)

                else:
                    raise Exception("Non-Symbol value found")

                # New item with dot position at start with each lookahead
                for rule in rules_table[next_symbol]:
                    new_item = StateItem(rule, 0, lookaheads)
                    if not new_item in closure_list:
                        new_items.append(new_item)
            
            # Add the new items
            old_len = len(closure_list)
            closure_list.extend(new_items)

            # Process new items
            for new_item in new_items:
                # If a similar item with the same rule and the same dot but a different lookahead exists
                has_base = list(StateItem.has_base_item(new_item, closure_list))
                lookaheads = []
                if has_base:
                    while has_base:
                        # Remove repeted
                        i = has_base.pop()
                        old_item = closure_list.pop(i)
                        lookaheads.extend(old_item.lookaheads)

                    # Merge lookaheads
                    closure_list.append(
                        StateItem(
                            old_item.production,
                            old_item.dot_position,
                            UniqueList(lookaheads),
                            old_item.transition
                        )
                    )

            # If state hasn't changed, break the loop
            if old_len == len(closure_list):
                has_changed = False

        self.items = UniqueTuple(closure_list)
    
    def goto(current_state: Self, target_symbol: str, rules_table: RulesTable, first_table: FirstTable) -> Self:
        # Calculates next state based on current state and the target symbol
        # Filter items from current state based on target symbol and current dot position (it shifts dot position by 1)
        new_state = State([
            StateItem(item.production, item.dot_position + 1, item.lookaheads) for item in current_state
            if item.dot_position < len(item.production.rhs) and item.production.rhs[item.dot_position] == target_symbol
        ])

        # Do closure to complete state with all production rules needed
        new_state.closure(rules_table, first_table)

        return new_state