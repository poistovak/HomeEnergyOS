from pathlib import Path


class EngineBuilder:
    def __init__(self):
        self.root = Path.cwd()

    def create_engine(self, name: str):

        module_name = name.lower()

        source = (
            self.root
            / "src"
            / "heos"
            / "result_verification"
            / f"{module_name}.py"
        )

        test = (
            self.root
            / "tests"
            / f"test_{module_name}_contract.py"
        )

        source.parent.mkdir(parents=True, exist_ok=True)
        test.parent.mkdir(parents=True, exist_ok=True)

        source.write_text(
            f'''class {self._class_name(module_name)}:

    def __init__(self):
        self.name = "{module_name}"

    def execute(self):
        return None
''',
            encoding="utf-8",
        )

        test.write_text(
            f'''from heos.result_verification.{module_name} import {self._class_name(module_name)}


def test_engine_exists():

    engine = {self._class_name(module_name)}()

    assert engine is not None
''',
            encoding="utf-8",
        )

        return [
            str(source),
            str(test),
        ]

    def _class_name(self, name: str):
        return "".join(
            part.capitalize()
            for part in name.split("_")
        )