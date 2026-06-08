class HomiError(Exception):
    """Base para todos os erros do compilador Homi."""

    def __init__(self, message: str, line: int = 0):
        self.line = line
        self.message = message
        prefix = f"[linha {line}] " if line else ""
        super().__init__(f"{prefix}{message}")

    def __str__(self):
        prefix = f"[linha {self.line}] " if self.line else ""
        return f"{self._kind} {prefix}{self.message}"

    _kind = "Erro"


class ErroLexico(HomiError):
    _kind = "Erro léxico"


class ErroSintatico(HomiError):
    _kind = "Erro sintático"


class ErroSemantico(HomiError):
    _kind = "Erro semântico"
