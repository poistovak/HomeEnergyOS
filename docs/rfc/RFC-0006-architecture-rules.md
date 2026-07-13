\# RFC-0007 — Core Decision Pipeline



\## Status

Accepted



\## Problem



HEOS must always make deterministic decisions.



Every decision follows exactly the same lifecycle.



No module may skip any step.



\---



\## Decision Pipeline



Sensor Data

↓



HouseState Builder

↓



Digital Twin

↓



Rule Engine

↓



Optimization Engine

↓



Decision Engine

↓



Safety Validator

↓



Action Queue

↓



Home Assistant



\---



\## Description



\### 1. Sensors



Collect raw information.



Examples:



\- PV

\- Battery

\- EV

\- Weather

\- Electricity price

\- User calendar

\- Presence



\---



\### 2. HouseState



Normalize all data.



Create one immutable snapshot.



\---



\### 3. Digital Twin



Predict future states.



Examples:



\- PV production

\- Battery SOC

\- EV arrival

\- Heat demand



\---



\### 4. Rule Engine



Apply Constitution and RFC rules.



\---



\### 5. Optimization Engine



Evaluate all possible strategies.



Examples:



\- Battery first

\- EV first

\- Sell energy

\- Buy energy



\---



\### 6. Decision Engine



Choose the best strategy.



\---



\### 7. Safety Validator



Reject unsafe actions.



Examples:



\- battery limits

\- breaker limits

\- user override



\---



\### 8. Action Queue



Produce executable commands.



No device communication happens before this stage.



\---



\## Architecture Rule



Every decision must pass through every stage.



Skipping stages is forbidden.

