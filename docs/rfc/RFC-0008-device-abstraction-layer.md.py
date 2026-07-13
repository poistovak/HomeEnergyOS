# RFC-0008 — Device Abstraction Layer

## Status

Accepted

---

## Problem

Decision Engine must never communicate with hardware directly.

HEOS shall work with any inverter, battery, charger or heat pump.

Hardware-specific code belongs only inside adapters.

---

## Architecture

Decision Engine

↓

Device Abstraction Layer

↓

Adapters

↓

Hardware

---

## Generic Devices

HEOS understands only generic devices.

### Battery

Functions

- charge(power)
- discharge(power)
- stop()

Properties

- soc
- capacity
- max_charge_power
- max_discharge_power

---

### EV Charger

Functions

- start()
- stop()
- set_power()

Properties

- connected
- charging
- vehicle_soc

---

### PV Inverter

Functions

- curtail()
- resume()

Properties

- production
- export_power

---

### Heat Source

Functions

- set_target_temperature()

Properties

- current_temperature
- mode

---

### House Load

Functions

- turn_on()
- turn_off()

---

## Rule

Decision Engine must never know:

- Fronius
- Victron
- Tesla
- Daikin
- Shelly
- Modbus
- MQTT
- REST

Decision Engine knows only interfaces.

---

## Benefits

- vendor independent

- testable

- future proof

- simulator compatible

- cloud compatible

- hardware replaceable