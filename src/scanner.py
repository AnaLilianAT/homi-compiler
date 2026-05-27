from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from .diagnostics import Diagnostic
from .tokens import KEYWORDS, SYMBOLS, Token, TokenType


class ScannerState(Enum):
    START = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    DURATION = auto()
    STRING = auto()
    COMMENT = auto()
    SYMBOL = auto()


ALLOWED_DURATION_UNITS = {"h", "min", "s"}


@dataclass
class ScannerResult:
    tokens: list[Token]
    diagnostics: list[Diagnostic]


@dataclass
class Scanner:
    source: str
    index: int = 0
    line: int = 1
    column: int = 1
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def scan_tokens(self) -> ScannerResult:
        tokens: list[Token] = []

        while not self._is_at_end():
            char = self._peek()
            state = ScannerState.START

            if char in {" ", "\t", "\r"}:
                self._advance()
                continue

            if char == "\n":
                tokens.append(Token(TokenType.NEWLINE, "\n", self.line, self.column))
                self._advance()
                continue

            if char == "#":
                state = ScannerState.COMMENT

            elif self._is_identifier_start(char):
                state = ScannerState.IDENTIFIER

            elif char.isdigit():
                state = ScannerState.NUMBER

            elif char == '"':
                state = ScannerState.STRING

            elif char in SYMBOLS:
                state = ScannerState.SYMBOL

            else:
                self.diagnostics.append(
                    Diagnostic(
                        message=f"Unexpected character '{char}'.",
                        line=self.line,
                        column=self.column,
                    )
                )
                self._advance()
                continue

            token = self._scan_state(state)
            if token is not None:
                tokens.append(token)

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return ScannerResult(tokens=tokens, diagnostics=list(self.diagnostics))

    def _scan_state(self, state: ScannerState) -> Token | None:
        if state is ScannerState.COMMENT:
            self._scan_comment()
            return None

        if state is ScannerState.IDENTIFIER:
            return self._scan_identifier_or_dotted_id()

        if state is ScannerState.NUMBER:
            return self._scan_number_or_duration()

        if state is ScannerState.STRING:
            return self._scan_string()

        if state is ScannerState.SYMBOL:
            return self._scan_symbol()

        return None

    def _scan_comment(self) -> None:
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _scan_identifier_or_dotted_id(self) -> Token:
        start_index = self.index
        start_line = self.line
        start_column = self.column
        state = ScannerState.IDENTIFIER
        saw_dot = False

        while not self._is_at_end():
            char = self._peek()

            if state is ScannerState.IDENTIFIER and self._is_identifier_part(char):
                self._advance()
                continue

            if char == "." and self._peek_next() is not None and self._is_identifier_start(self._peek_next()):
                saw_dot = True
                self._advance()
                state = ScannerState.IDENTIFIER
                continue

            break

        lexeme = self.source[start_index:self.index]
        if saw_dot:
            token_type = TokenType.DOTTED_ID
        else:
            token_type = KEYWORDS.get(lexeme, TokenType.IDENTIFIER)

        return Token(token_type, lexeme, start_line, start_column)

    def _scan_number_or_duration(self) -> Token:
        start_index = self.index
        start_line = self.line
        start_column = self.column
        state = ScannerState.NUMBER
        has_decimal = False

        while not self._is_at_end():
            char = self._peek()

            if state is ScannerState.NUMBER and char.isdigit():
                self._advance()
                continue

            if state is ScannerState.NUMBER and char == "." and not has_decimal and self._peek_next() is not None and self._peek_next().isdigit():
                has_decimal = True
                self._advance()
                continue

            if state is ScannerState.NUMBER and char.isalpha():
                state = ScannerState.DURATION
                if not self._consume_duration_suffix():
                    self.diagnostics.append(
                        Diagnostic(
                            message="Invalid duration literal.",
                            line=start_line,
                            column=start_column,
                        )
                    )
                break

            break

        lexeme = self.source[start_index:self.index]
        token_type = TokenType.DURATION if state is ScannerState.DURATION else TokenType.NUMBER
        return Token(token_type, lexeme, start_line, start_column)

    def _consume_duration_suffix(self) -> bool:
        if not self._consume_duration_unit():
            self._consume_invalid_duration_tail()
            return False

        while not self._is_at_end() and self._peek().isdigit():
            while not self._is_at_end() and self._peek().isdigit():
                self._advance()

            if not self._consume_duration_unit():
                self._consume_invalid_duration_tail()
                return False

        return True

    def _consume_duration_unit(self) -> bool:
        if self._is_at_end() or not self._peek().isalpha():
            return False

        unit_start = self.index
        while not self._is_at_end() and self._peek().isalpha():
            self._advance()

        return self.source[unit_start:self.index] in ALLOWED_DURATION_UNITS

    def _consume_invalid_duration_tail(self) -> None:
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()

    def _scan_string(self) -> Token | None:
        start_index = self.index
        start_line = self.line
        start_column = self.column
        state = ScannerState.STRING
        escaped = False

        self._advance()

        while not self._is_at_end():
            char = self._peek()

            if state is ScannerState.STRING and escaped:
                escaped = False
                self._advance()
                continue

            if char == "\\":
                escaped = True
                self._advance()
                continue

            if char == '"':
                self._advance()
                lexeme = self.source[start_index:self.index]
                return Token(TokenType.STRING, lexeme, start_line, start_column)

            if char == "\n":
                self.diagnostics.append(
                    Diagnostic(
                        message="Unterminated string literal.",
                        line=start_line,
                        column=start_column,
                    )
                )
                return None

            self._advance()

        self.diagnostics.append(
            Diagnostic(
                message="Unterminated string literal.",
                line=start_line,
                column=start_column,
            )
        )
        return None

    def _scan_symbol(self) -> Token:
        start_line = self.line
        start_column = self.column
        char = self._advance()
        return Token(SYMBOLS[char], char, start_line, start_column)

    def _peek(self) -> str:
        return self.source[self.index]

    def _peek_next(self) -> str | None:
        next_index = self.index + 1
        if next_index >= len(self.source):
            return None
        return self.source[next_index]

    def _advance(self) -> str:
        char = self.source[self.index]
        self.index += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def _is_at_end(self) -> bool:
        return self.index >= len(self.source)

    @staticmethod
    def _is_identifier_start(char: str) -> bool:
        return char.isalpha() or char == "_"

    @staticmethod
    def _is_identifier_part(char: str) -> bool:
        return char.isalnum() or char == "_"
