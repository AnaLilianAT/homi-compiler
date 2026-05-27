from __future__ import annotations

from dataclasses import dataclass, field

from .grammar import ENDMARKER, EPSILON, NON_TERMINALS, PRODUCTIONS, START_SYMBOL, TERMINALS


SYNC_TOKENS = {"SEMICOLON", "RBRACE", "RBRACKET", "EOF"}


@dataclass(slots=True)
class PredictiveParsingTable:
    table: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    first_sets: dict[str, set[str]] = field(default_factory=dict)
    follow_sets: dict[str, set[str]] = field(default_factory=dict)

    def get(self, non_terminal: str, terminal: str) -> list[str] | None:
        return self.table.get(non_terminal, {}).get(terminal)


def build_default_table() -> PredictiveParsingTable:
    first_sets = _compute_first_sets()
    follow_sets = _compute_follow_sets(first_sets)
    table: dict[str, dict[str, list[str]]] = {non_terminal: {} for non_terminal in NON_TERMINALS}

    for non_terminal, productions in PRODUCTIONS.items():
        for production in productions:
            first_of_production = _first_of_sequence(production, first_sets)

            for terminal in first_of_production - {EPSILON}:
                _store_production(table, non_terminal, terminal, production)

            if EPSILON in first_of_production:
                for follow_terminal in follow_sets[non_terminal]:
                    _store_production(table, non_terminal, follow_terminal, production)

    return PredictiveParsingTable(table=table, first_sets=first_sets, follow_sets=follow_sets)


def _store_production(
    table: dict[str, dict[str, list[str]]],
    non_terminal: str,
    terminal: str,
    production: list[str],
) -> None:
    existing = table[non_terminal].get(terminal)
    if existing is not None and existing != production:
        raise ValueError(
            f"Grammar is not LL(1): conflict at ({non_terminal}, {terminal}) "
            f"between {existing} and {production}."
        )
    table[non_terminal][terminal] = production


def _compute_first_sets() -> dict[str, set[str]]:
    first_sets: dict[str, set[str]] = {symbol: set() for symbol in NON_TERMINALS}

    changed = True
    while changed:
        changed = False

        for non_terminal, productions in PRODUCTIONS.items():
            for production in productions:
                before = len(first_sets[non_terminal])
                first_sets[non_terminal].update(
                    _first_of_sequence(production, first_sets, allow_partial=True)
                )
                if len(first_sets[non_terminal]) != before:
                    changed = True

    return first_sets


def _compute_follow_sets(first_sets: dict[str, set[str]]) -> dict[str, set[str]]:
    follow_sets: dict[str, set[str]] = {symbol: set() for symbol in NON_TERMINALS}
    follow_sets[START_SYMBOL].add(ENDMARKER)

    changed = True
    while changed:
        changed = False

        for non_terminal, productions in PRODUCTIONS.items():
            for production in productions:
                trailer = set(follow_sets[non_terminal])

                for symbol in reversed(production):
                    if symbol == EPSILON:
                        continue

                    if symbol in NON_TERMINALS:
                        before = len(follow_sets[symbol])
                        follow_sets[symbol].update(trailer)
                        if len(follow_sets[symbol]) != before:
                            changed = True

                        symbol_first = first_sets[symbol]
                        if EPSILON in symbol_first:
                            trailer = trailer | (symbol_first - {EPSILON})
                        else:
                            trailer = set(symbol_first)
                    else:
                        trailer = {symbol}

    return follow_sets


def _first_of_sequence(
    sequence: list[str],
    first_sets: dict[str, set[str]],
    allow_partial: bool = False,
) -> set[str]:
    if sequence == [EPSILON]:
        return {EPSILON}

    result: set[str] = set()
    can_derive_epsilon = True

    for symbol in sequence:
        if symbol == EPSILON:
            result.add(EPSILON)
            break

        if symbol in TERMINALS:
            result.add(symbol)
            can_derive_epsilon = False
            break

        if symbol in NON_TERMINALS:
            symbol_first = first_sets[symbol]
            result.update(symbol_first - {EPSILON})
            if EPSILON in symbol_first:
                continue

            can_derive_epsilon = False
            break

        if allow_partial:
            can_derive_epsilon = False
            break

        raise KeyError(f"Unknown grammar symbol: {symbol}")

    if can_derive_epsilon:
        result.add(EPSILON)

    return result
