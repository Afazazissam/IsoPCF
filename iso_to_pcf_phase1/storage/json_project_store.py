from __future__ import annotations

import json
from pathlib import Path

from models.project import Project


class JsonProjectStore:
    def save(self, project: Project, path: str | Path) -> None:
        project.touch()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(project.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self, path: str | Path) -> Project:
        source = Path(path)
        data = json.loads(source.read_text(encoding="utf-8"))
        return Project.from_dict(data)
