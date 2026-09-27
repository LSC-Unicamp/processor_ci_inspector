"""Bounded, serializable expressions for observable register-file ports."""

EXPRESSION_VERSION = 1
ARCHITECTURAL_EXPRESSION_VERSION = 2
EXPRESSION_PREFIX = "__expression__:"
_OPS = {"signal", "constant", "slice", "concat", "not", "and", "or", "eq", "ne", "mux"}
_V2_OPS = {"priority_mux", "add", "shift_left", "zero_extend", "sign_extend", "mask"}


def expression_paths(expr, _depth=0, *, version=EXPRESSION_VERSION):
    if version not in (EXPRESSION_VERSION, ARCHITECTURAL_EXPRESSION_VERSION):
        raise ValueError("unsupported interface expression version")
    if not isinstance(expr, dict) or expr.get("op") not in (
        _OPS | (_V2_OPS if version == ARCHITECTURAL_EXPRESSION_VERSION else set())
    ):
        raise ValueError("invalid register-file interface expression")
    if _depth > (8 if version == ARCHITECTURAL_EXPRESSION_VERSION else 5):
        raise ValueError("interface expression is too deep")
    op = expr["op"]
    if op == "priority_mux":
        cases = expr.get("cases")
        default = expr.get("default")
        if (not isinstance(cases, list) or not 1 <= len(cases) <= 7
                or not all(isinstance(case, dict) and set(case) == {"when", "value"}
                           for case in cases)
                or default != {"op": "constant", "value": 0}):
            raise ValueError("invalid architectural priority mux")
        paths = set()
        for case in cases:
            paths.update(expression_paths(case["when"], _depth + 1, version=version))
            paths.update(expression_paths(case["value"], _depth + 1, version=version))
        if len(paths) > 16:
            raise ValueError("architectural expression uses too many signals")
        return paths
    if op == "add":
        args = expr.get("args")
        width = expr.get("width")
        if (not isinstance(args, list) or len(args) != 2
                or not isinstance(width, int) or not 1 <= width <= 256):
            raise ValueError("invalid architectural add")
    elif op == "shift_left":
        args = expr.get("args")
        amount, width = expr.get("amount"), expr.get("width")
        if (not isinstance(args, list) or len(args) != 1
                or not isinstance(amount, int) or not 0 <= amount <= 255
                or not isinstance(width, int) or not 1 <= width <= 256):
            raise ValueError("invalid architectural shift")
    elif op in ("zero_extend", "sign_extend"):
        args = expr.get("args")
        from_width, to_width = expr.get("from_width"), expr.get("to_width")
        if (not isinstance(args, list) or len(args) != 1
                or not isinstance(from_width, int) or not isinstance(to_width, int)
                or not 1 <= from_width <= to_width <= 256):
            raise ValueError("invalid architectural extension")
    elif op == "mask":
        args = expr.get("args")
        width = expr.get("width")
        if (not isinstance(args, list) or len(args) != 1
                or not isinstance(width, int) or not 1 <= width <= 256):
            raise ValueError("invalid architectural mask")
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
    if op in _V2_OPS:
        expected = {"add": 2, "shift_left": 1, "zero_extend": 1,
                    "sign_extend": 1, "mask": 1}
        if len(args) != expected[op]:
            raise ValueError("invalid architectural expression arity")
        paths = set()
        for arg in args:
            paths.update(expression_paths(arg, _depth + 1, version=version))
        if len(paths) > 16:
            raise ValueError("architectural expression uses too many signals")
        return paths
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
        paths.update(expression_paths(arg, _depth + 1, version=version))
    if len(paths) > (16 if version == ARCHITECTURAL_EXPRESSION_VERSION else 4):
        raise ValueError("interface expression uses too many signals")
    return paths


def evaluate_expression(expr, values):
    """Evaluate a small AST; unresolved leaves propagate as None."""
    op = expr.get("op") if isinstance(expr, dict) else None
    if op == "signal":
        return values.get(expr.get("path"))
    if op == "constant":
        return int(expr["value"])
    if op == "priority_mux":
        for case in expr.get("cases", []):
            selected = evaluate_expression(case["when"], values)
            if selected is None:
                return None
            if selected:
                return evaluate_expression(case["value"], values)
        return evaluate_expression(expr["default"], values)
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
    if op == "add" and len(operands) == 2:
        width = int(expr["width"])
        return (operands[0] + operands[1]) & ((1 << width) - 1)
    if op == "shift_left" and len(operands) == 1:
        width = int(expr["width"])
        return (operands[0] << int(expr["amount"])) & ((1 << width) - 1)
    if op == "mask" and len(operands) == 1:
        return operands[0] & ((1 << int(expr["width"])) - 1)
    if op == "zero_extend" and len(operands) == 1:
        return operands[0] & ((1 << int(expr["from_width"])) - 1)
    if op == "sign_extend" and len(operands) == 1:
        from_width = int(expr["from_width"])
        to_width = int(expr["to_width"])
        value = operands[0] & ((1 << from_width) - 1)
        if value & (1 << (from_width - 1)):
            value |= ((1 << to_width) - 1) ^ ((1 << from_width) - 1)
        return value & ((1 << to_width) - 1)
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

    def __init__(self, expression, resolve, read, role, version=EXPRESSION_VERSION):
        self.expression = expression
        self._path = f"{EXPRESSION_PREFIX}{role}"
        self._read = read
        self._handles = {}
        for path in expression_paths(expression, version=version):
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
