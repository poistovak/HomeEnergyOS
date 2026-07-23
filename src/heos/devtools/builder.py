from __future__ import annotations

from pathlib import Path


class EngineBuilder:

    def create_engine(
        self,
        name: str,
    ) -> list[Path]:

        if not name.strip():
            raise ValueError(
                "name must not be empty"
            )

        module_name = name.lower()

        return [
            Path(
                f"src/heos/result_verification/{module_name}.py"
            ),
            Path(
                f"tests/test_{module_name}_contract.py"
            ),
        ]