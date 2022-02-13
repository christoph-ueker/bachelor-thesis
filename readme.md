# Learning UPPAAL Timed Automata from Network Protocol Traces
This is the official python project for the bachelor thesis of **Christoph Ueker**.

## About the Bachelor Thesis
| Title | Learning UPPAAL Timed Automata from Network Protocol Traces
| --- | --- |
| Student | **Christoph Ueker**
| Working period | 15.11.2021 - **15.02.2022**
| University | Hamburg University of Technology (TUHH)
| Insitute | Institute for Software Systems
| Supervised by | Prof. Dr. Sibylle Schupp, Antje Rogalla

## About this Python Project
### General
| What was used | How it was used
| --- | --- |
| Python  | version 3.8.2
| PyCharm | version 2021.2.2 (Community Edition)
| Windows | Windows 10 Pro version 21H1
| Packages| See _requirements.txt_

### Project folders
The folder _UPPAAL-Stratego_ contains the UPPAAL Stratego version 4.1.20-7 downloaded from [uppaal.org](https://uppaal.org/downloads/).
It contains _uppaal.jar_, which will run the created UPPAAL Model automatically. It also contains an executable called _verifyta_,
which is used in order to run a _simulate_ query.

The folder _uppaalpy_ contains the module uppaalpy, which is a UPPAAL wrapper for python by Deniz Koluaçık.
The used version 0.0.4 was committed on June 8th, 2021 downloaded from his [github repository](https://github.com/koluacik/uppaal-py).
**WARNING: The module has been adjusted in order to work properly and to make things easier**
(Look for comments stating "adjusted" in _nta.py_).

The folder _original_logs_ contains the logs given as examples in the original paper "Learning Timed Automata from Interaction Traces"
by Vain et al.

The folder _xml-files_ contains all Uppaal Timed Automata given as .xml files used throughout the project.

### Program flow
1. Running **main.py** will run **simulator.py** first, asking the user for the interval abstraction parameter value (R), the number of environment nodes to be modelled
and the desired number of simulations used in order to generate traces using the _simulator.xml_.
2. **simulator.py** produces _simulator_output.xml_ and _query.q_ in order to use them in a **verifyta** command. The
command writes the resulting simulation output to _simulations.txt_. Both files can be found in _UPPAAL-Stratego/bin-Windows/_.
3. The **conerter.py** translates the simulation output to useful traces by applying a **mapping**.
4. The produced traces will then be used by the algorithm implemented in **main.py**.
5. **main.py** uses the library **uppaalpy** in order to create an UPPAAL system and later write it to _output.xml_.
6. UPPAAL Stratego will be run in order to view the result.

### Comments
- Helper functions have been outsourced to _hepler.py_
- Functions have been commented using [docstrings](https://www.jetbrains.com/help/pycharm/using-docstrings-to-specify-types.html), working nicely in PyCharm
- _trace_converter_manual.py_ is an old backup module not part of the working code anymore
