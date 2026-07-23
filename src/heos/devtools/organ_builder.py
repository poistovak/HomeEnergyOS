from pathlib import Path
import json


class OrganBuilder:

    def __init__(self):
        self.root = Path.cwd()

    def create_organ(self, name: str):

        organ_name = name.lower()

        organ_path = (
            self.root
            / "src"
            / "heos"
            / "organs"
            / organ_name
        )

        test_path = (
            self.root
            / "tests"
            / f"test_{organ_name}_organ_contract.py"
        )

        organ_path.mkdir(parents=True, exist_ok=True)

        files = []

        # identity
        (organ_path / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )

        files.append(organ_path / "__init__.py")


        # main organ
        (organ_path / "organ.py").write_text(
            f'''class {self._class_name(organ_name)}Organ:

    def __init__(self):
        self.name = "{organ_name}"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
''',
            encoding="utf-8",
        )

        files.append(organ_path / "organ.py")


        # state
        (organ_path / "state.py").write_text(
            '''class OrganState:

    def __init__(self):
        self.status = "new"
''',
            encoding="utf-8",
        )

        files.append(organ_path / "state.py")


        # memory
        (organ_path / "memory.py").write_text(
            '''class OrganMemory:

    def __init__(self):
        self.records = []
''',
            encoding="utf-8",
        )

        files.append(organ_path / "memory.py")


        # contract
        (organ_path / "contract.py").write_text(
            f'''ORGAN_NAME = "{organ_name}"

REQUIRED_STATUS = "active"
''',
            encoding="utf-8",
        )

        files.append(organ_path / "contract.py")


        # manifest
        (organ_path / "manifest.json").write_text(
            json.dumps(
                {
                    "name": organ_name,
                    "type": "heos-organ",
                    "status": "initialized",
                },
                indent=4,
            ),
            encoding="utf-8",
        )

        files.append(organ_path / "manifest.json")


        # test
        test_path.write_text(
            f'''from heos.organs.{organ_name}.organ import {self._class_name(organ_name)}Organ


def test_organ_exists():

    organ = {self._class_name(organ_name)}Organ()

    assert organ is not None
''',
            encoding="utf-8",
        )

        files.append(test_path)

        return [str(f) for f in files]


    def _class_name(self, name: str):

        return "".join(
            part.capitalize()
            for part in name.split("_")
        )