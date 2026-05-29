from __future__ import annotations

import re


class IdGenerator:
    @staticmethod
    def next_id(prefix: str, existing_ids: list[str] | set[str], width: int = 3) -> str:
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
        highest = 0
        for value in existing_ids:
            match = pattern.match(value)
            if match:
                highest = max(highest, int(match.group(1)))
        return f"{prefix}{highest + 1:0{width}d}"
