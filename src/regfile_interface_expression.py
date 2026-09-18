"""Bounded, serializable expressions for observable register-file ports."""

EXPRESSION_VERSION = 1
EXPRESSION_PREFIX = "__expression__:"
_OPS = {"signal", "constant", "slice", "concat", "not", "and", "or", "eq", "ne", "mux"}


def expression_paths(expr, _depth=0):
    if not isinstance(expr, dict) or expr.get("op") not in _OPS:
        raise ValueError("invalid register-file interface expression")
    if _depth > 5:
        raise ValueError("interface expression is too deep")
    op = expr["op"]
    if op == "signal":
        path = expr.get("path")
        if not isinstance(path, str) or not path or path.startswith("__"):
            raise ValueError("invalid interface signal path")
        return {path}
    if op == "constant":
        if not isinstance(expr.get("value"), int):
            raise ValueError("invalid expression constant")
        return set()
    args = expr.get("args")
    expected = {"slice": (1,), "not": (1,), "eq": (2,), "ne": (2,),
                "mux": (3,), "and": (2, 3, 4), "or": (2, 3, 4),
                "concat": (2, 3, 4)}
    if not isinstance(args, list) or len(args) not in expected[op]:
        raise ValueError("invalid expression arity")
    if op == "slice" and (
        not isinstance(expr.get("lsb"), int) or not isinstance(expr.get("width"), int)
        or expr["lsb"] < 0 or not 1 <= expr["width"] <= 256
    ):
        raise ValueError("invalid expression slice")
    if op == "concat" and (
        not isinstance(expr.get("widths"), list)
        or len(expr["widths"]) != len(args)
        or any(not isinstance(width, int) or not 1 <= width <= 256 for width in expr["widths"])
    ):
        raise ValueError("invalid expression concatenation")
    paths = set()
    for arg in args:
        paths.update(expression_paths(arg, _depth + 1))
    if len(paths) > 4:
        raise ValueError("interface expression uses too many signals")
    return paths


def evaluate_expression(expr, values):
    """Evaluate a small AST; unresolved leaves propagate as None."""
    op = expr.get("op") if isinstance(expr, dict) else None
    if op == "signal":
        return values.get(expr.get("path"))
    if op == "constant":
        return int(expr["value"])
    args = expr.get("args", []) if isinstance(expr, dict) else []
    operands = [evaluate_expression(arg, values) for arg in args]
    if any(value is None for value in operands):
        return None
    if op == "slice" and len(operands) == 1:
        lsb, width = int(expr["lsb"]), int(expr["width"])
        if lsb < 0 or width < 1 or width > 256:
            return None
        return (operands[0] >> lsb) & ((1 << width) - 1)
    if op == "concat" and operands and len(operands) == len(expr.get("widths", [])):
        result = 0
        for value, width in zip(operands, expr["widths"]):
            width = int(width)
            if width < 1 or width > 256:
                return None
            result = (result << width) | (value & ((1 << width) - 1))
        return result
    if op == "not" and len(operands) == 1:
        return int(not operands[0])
    if op == "and" and operands:
        return int(all(operands))
    if op == "or" and operands:
        return int(any(operands))
    if op in ("eq", "ne") and len(operands) == 2:
        return int((operands[0] == operands[1]) == (op == "eq"))
    if op == "mux" and len(operands) == 3:
        return operands[1] if operands[0] else operands[2]
    raise ValueError("unsupported register-file interface expression")


class ExpressionHandle:
    """Read-only handle facade for existing cocotb-facing consumers."""

    def __init__(self, expression, resolve, read, role):
        self.expression = expression
        self._path = f"{EXPRESSION_PREFIX}{role}"
        self._read = read
        self._handles = {}
        for path in expression_paths(expression):
            handle = resolve(path)
            if handle is None:
                raise ValueError(f"unresolvable expression leaf: {path}")
            self._handles[path] = handle

    @property
    def value(self):
        return evaluate_expression(
            self.expression,
            {path: self._read(handle) for path, handle in self._handles.items()},
        )
