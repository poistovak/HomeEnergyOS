from __future__ import annotations

import sys

from heos.devtools import EngineBuilder, OrganBuilder


def main() -> None:

    if len(sys.argv) < 3:
        print(
            "usage: heos <command> <name>"
        )
        return

    command = sys.argv[1]
    name = sys.argv[2]


    if command == "create-engine":

        builder = EngineBuilder()

        files = builder.create_engine(name)

        for file in files:
            print(file)

        return


    if command == "create-organ":

        builder = OrganBuilder()

        files = builder.create_organ(name)

        for file in files:
            print(file)

        return


    print(f"unknown command: {command}")


if __name__ == "__main__":
    main()