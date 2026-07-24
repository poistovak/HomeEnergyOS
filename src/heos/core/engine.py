from dataclasses import dataclass


@dataclass
class Engine:

    def tick(self):

        print("===================================")
        print("        HEOS Decision Engine")
        print("===================================")

        print("1. Collect sensors")
        print("2. Build HouseState")
        print("3. Run Digital Twin")
        print("4. Execute Rule Engine")
        print("5. Optimize")
        print("6. Validate Safety")
        print("7. Build Action Queue")

        print()
        print("HEOS heartbeat complete.")