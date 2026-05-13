from __future__ import annotations


def scalar(value) -> str:
    """Return a compact TOON-style scalar safe for one-line prompts."""
    text = str(value)
    return text.replace("\\", "\\\\").replace("\r", " ").replace("\n", " ").strip()


def mapping(fields: dict[str, object]) -> str:
    return "\n".join(f"{key}: {scalar(value)}" for key, value in fields.items())


def rows(name: str, fields: list[str], items: list[dict[str, object]]) -> str:
    header = f"{name}[{len(items)}]{{{','.join(fields)}}}:"
    if not items:
        return header

    body = [
        "  " + ",".join(scalar(item.get(field, "")) for field in fields)
        for item in items
    ]
    return "\n".join([header, *body])
