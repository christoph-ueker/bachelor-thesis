# Learning UPPAAL Timed Automata from Network Protocol Traces
This is the official python project for the bachelor thesis of **Christoph Ueker**.

## About this Python Project
### General
| What was used | How it was used
| --- | --- |
| Python  | version 3.8.2
| PyCharm | version 2021.2.2 (Community Edition)
| Windows | Windows 10 Pro version 21H1

### Project folders
The folder _UPPAAL-Stratego_ contains the UPPAAL Stratego version 4.1.20-7 downloaded from [uppaal.org](https://uppaal.org/downloads/).
It contains _uppaal.jar_, which will run the created UPPAAL Model automatically. It also contains an executable called _verifyta_,
which is used in order to run a _simulate_ query.

The folder _uppaalpy_ contains the module uppaalpy, which is a UPPAAL wrapper for python by Deniz Koluaçık.
The used version is from June 8th 2021, downloaded from his [github repository](https://github.com/koluacik/uppaal-py).
**WARNING: The module has been adjusted in order to work properly and to make things easier**
(Look for comments stating "adjusted").

### Program flow
1. Running **main.py** will run **simulator.py** first, asking the user for the number of environment nodes to be modelled
and the desired number of simulations used in order to generate traces using the _simulator.xml_.
2. **simulator.py** produces _simulator_output.xml_ and _query.q_ in order to use them in a **verifyta** command. The
command writes the resulting simulation output to _simulations.txt_.
3. The **trace_conerter.py** translates the simulation output to useful traces by applying a **mapping**.
4. The produced traces will then be used by the algorithm implemented in **main.py**, asking the user for a parameter,
which has to be given before running the algo itself.
5. **main.py** uses the library **uppaalpy** in order to create an UPPAAL system and later write it to _output.xml_.
6. UPPAAL Stratego will be run in order to view the result.

## About the Bachelor Thesis
| Title | Learning UPPAAL Timed Automata from Network Protocol Traces
| --- | --- |
| Student | **Christoph Ueker**
| Working period | 15.11.2021 - **15.02.2022**
| University | Hamburg University of Technology (TUHH)
| Insitute | Institute for Software Systems
| Supervised by | Prof. Dr. Sibylle Schupp, Antje Rogalla
