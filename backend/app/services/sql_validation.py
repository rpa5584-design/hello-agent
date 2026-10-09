"""Conservative SELECT parser; validates without opening or executing SQLite.

Unsupported SQL (including subqueries, CTEs, unions, comments and OFFSET) is
rejected. Future execution must still use a read-only connection/authorizer.
"""

import re
from dataclasses import dataclass

MAX_ROWS = 20
TABLES = {
    "saved_hotels": {"hotel_id", "name", "address", "latitude", "longitude"},
    "saved_hotel_zips": {"hotel_id", "zip_code", "latitude", "longitude", "locality", "country_code"},
    "demo_hotel_nights": {"hotel_id", "stay_date", "nightly_rate_cents", "rooms_available"},
}
FUNCTIONS = {"count", "sum", "min", "max", "avg", "round", "coalesce", "lower", "upper"}
KEYWORDS = set("select distinct from join inner left outer on where group by having order asc desc limit as and or not is null in between like".split())
FORBIDDEN = set("insert update delete drop alter create replace pragma attach detach vacuum with union intersect except explain".split())
LEXER = re.compile(r"\s+|'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|<=|>=|<>|!=|[(),.*+/%=<>;-]")


class SqlValidationError(ValueError):
    """Model output is outside the supported read-only SELECT subset."""


@dataclass(frozen=True)
class ValidatedSql:
    sql: str
    tables: tuple[str, ...]
    proposed_sql: str


class _SelectParser:
    def __init__(self, sql: str):
        self.sql = sql
        self.tokens = []
        position = 0
        while position < len(sql):
            match = LEXER.match(sql, position)
            if not match:
                self.fail()
            token = match.group()
            if not token.isspace():
                self.tokens.append((token, match.start(), match.end()))
            position = match.end()
        if self.tokens and self.tokens[-1][0] == ";":
            self.tokens.pop()
        if len(self.tokens) > 2000 or any(
            (a[0], b[0]) in {("-", "-"), ("/", "*"), ("*", "/")}
            for a, b in zip(self.tokens, self.tokens[1:])
        ):
            self.fail()
        if any(t[0] == ";" or t[0].lower() in FORBIDDEN for t in self.tokens):
            self.fail()
        self.index = 0
        self.aliases = {}
        self.references = []
        self.output_aliases = set()

    def fail(self):
        raise SqlValidationError("Proposed SQL is outside the approved bounded SELECT rules.")

    def peek(self):
        return self.tokens[self.index][0].lower() if self.index < len(self.tokens) else ""

    def take(self):
        if self.index >= len(self.tokens):
            self.fail()
        token = self.tokens[self.index][0]
        self.index += 1
        return token

    def accept(self, token):
        if self.peek() == token:
            self.take()
            return True
        return False

    def expect(self, token):
        if not self.accept(token):
            self.fail()

    def identifier(self):
        token = self.take()
        if token.startswith('"'):
            token = token[1:-1].replace('""', '"')
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", token) or token.lower() in KEYWORDS | FORBIDDEN:
            self.fail()
        return token.lower()

    def expression(self, minimum=0):
        if self.peek() in {"not", "+", "-"}:
            self.take()
            self.expression(7)
        elif self.accept("("):
            self.expression()
            self.expect(")")
        elif self.peek().startswith("'") or re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", self.peek()) or self.peek() == "null":
            self.take()
        elif self.accept("*"):
            pass
        else:
            name = self.identifier()
            if self.accept("("):
                if name not in FUNCTIONS:
                    self.fail()
                self.accept("distinct")
                self.expression()
                while self.accept(","):
                    self.expression()
                self.expect(")")
            elif self.accept("."):
                column = "*" if self.accept("*") else self.identifier()
                self.references.append((name, column))
            else:
                self.references.append((None, name))
        precedence = {"or": 1, "and": 2, "=": 3, "!=": 3, "<>": 3, "<": 3, ">": 3, "<=": 3, ">=": 3, "is": 3, "in": 3, "like": 3, "between": 3, "+": 4, "-": 4, "*": 5, "/": 5, "%": 5}
        while self.peek() in precedence and precedence[self.peek()] >= minimum:
            operator = self.take().lower()
            level = precedence[operator]
            if operator == "in":
                self.expect("(")
                self.expression()
                while self.accept(","):
                    self.expression()
                self.expect(")")
            elif operator == "between":
                self.expression(level + 1)
                self.expect("and")
                self.expression(level + 1)
            else:
                if operator == "is":
                    self.accept("not")
                self.expression(level + 1)

    def table(self):
        table = self.identifier()
        if table not in TABLES:
            self.fail()
        alias = table
        if self.accept("as"):
            alias = self.identifier()
        elif self.peek() and self.peek() not in KEYWORDS and (self.peek().startswith('"') or re.fullmatch(r"[a-z_][a-z_0-9]*", self.peek())):
            alias = self.identifier()
        if alias in self.aliases:
            self.fail()
        self.aliases[alias] = table

    def parse(self):
        self.expect("select")
        self.accept("distinct")
        while True:
            self.expression()
            if self.accept("as"):
                self.output_aliases.add(self.identifier())
            if not self.accept(","):
                break
        self.expect("from")
        self.table()
        while self.peek() in {"join", "inner", "left"}:
            if self.accept("left"):
                self.accept("outer")
            else:
                self.accept("inner")
            self.expect("join")
            self.table()
            self.expect("on")
            self.expression()
        if self.accept("where"):
            self.expression()
        if self.accept("group"):
            self.expect("by")
            self.expression()
            while self.accept(","):
                self.expression()
        if self.accept("having"):
            self.expression()
        if self.accept("order"):
            self.expect("by")
            while True:
                self.expression()
                if not self.accept("asc"):
                    self.accept("desc")
                if not self.accept(","):
                    break
        self.expect("limit")
        limit_token = self.tokens[self.index] if self.index < len(self.tokens) else None
        limit = self.take()
        if not re.fullmatch(r"[0-9]+", limit) or int(limit) <= 0 or self.index != len(self.tokens):
            self.fail()
        for alias, column in self.references:
            if alias is not None:
                if alias not in self.aliases or (column != "*" and column not in TABLES[self.aliases[alias]]):
                    self.fail()
            elif column not in self.output_aliases and not any(column in TABLES[t] for t in self.aliases.values()):
                self.fail()
        sql = self.sql[:limit_token[1]] + str(min(int(limit), MAX_ROWS))
        return ValidatedSql(sql.strip(), tuple(sorted(set(self.aliases.values()))), self.sql)


def validate_sql(sql: str) -> ValidatedSql:
    if not isinstance(sql, str) or not sql.strip() or len(sql) > 12000:
        raise SqlValidationError("A bounded SELECT proposal is required.")
    try:
        return _SelectParser(sql.strip()).parse()
    except (RecursionError, ValueError) as error:
        if isinstance(error, SqlValidationError):
            raise
        raise SqlValidationError("Proposal is too complex or malformed.") from None
