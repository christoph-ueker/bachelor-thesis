"""
This module takes the basic simulation xml file and adjusts it to the
desired Env node count and simulation count (aka. the number of traces).
"""

from uppaalpy import nta as u

nodes = int(input("How many Env nodes?:\n"))
# simulations = int(input("How many simulations?:\n"))

# load the basic model build from the paper
sys = u.NTA.from_xml(path='xml-files/simulator.xml')


# --- Global declarations ---
global_decls = "// Place global declarations here.\nbroadcast chan "
for i in range(1, nodes+1):
    if i > 1:
        global_decls += ", "
    global_decls += "Req" + str(i) + "x0, Ack" + str(i) + "x0, Req0x" + str(i) + ", Ack0x" + str(i)

global_decls += ";\nint TO10 = 8;\nint TO100 = 3;\n"
for i in range(1, nodes+1):
    global_decls += "int c" + str(i) + " = -1;\n"

print(global_decls)
# sys.declaration = u.Declaration(global_decls)

# --- System declarations ---
system_decls = "// Place template instantiations here.\n"
templ_instant = ""
proc_comp = "\n // List one or more processes to be composed into a system.\nsystem "

for i in range(1, nodes+1):
    templ_instant += "Node" + str(i) + " = NodeENV" + str(i) + "();\n"
    if i > 1:
        proc_comp += ", "
    proc_comp += "Node" + str(i)
proc_comp += ";"
system_decls += templ_instant + proc_comp

print(system_decls)
