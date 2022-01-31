"""
This module takes the basic simulation xml file and adjusts it to the
desired Env node count and simulation count (aka. the number of traces).
"""
import os
import subprocess
from uppaalpy import nta as u

# nodes = int(input("How many Env nodes?:\n"))
nodes = 10
# simulations = int(input("How many simulations?:\n"))
simulations = 1000
# We need a bonus simulation in order to drop it lateron due to weird simulation savings by UPPAAL
simulations += 1

print("Simulator is running now...")

# load the basic model build from the paper
sys = u.NTA.from_xml(path='xml-files/simulator.xml')

# --- Global declarations ---
# global_decls = "// Place global declarations here.\n// We need 'broadcast' here in order to run simulations." \
#                "\nbroadcast chan "
# for i in range(1, nodes+1):
#     if i > 1:
#         global_decls += ", "
#     global_decls += "Req" + str(i) + "x0, Ack" + str(i) + "x0, Req0x" + str(i) + ", Ack0x" + str(i)

# global_decls += ";\n"
# for i in range(1, nodes+1):
#     global_decls += "int c" + str(i) + " = -1;\n"
#
# print(global_decls)
# sys.declaration = u.Declaration(global_decls)

# --- System declarations ---

system_decls = "// Place template instantiations here.\nint "
templ_instant = ""
proc_comp = "\n // List one or more processes to be composed into a system.\nsystem "

for i in range(nodes):
    if i > 0:
        system_decls += ", "
    system_decls += "c" + str(i) + " = -1"
system_decls += ";\n"

for i in range(nodes):
    templ_instant += "Node" + str(i) + " = NodeENV" + "(c" + str(i) + ", " + str(i) + ");\n"
    if i > 0:
        proc_comp += ", "
    proc_comp += "Node" + str(i)
proc_comp += ";"
system_decls += templ_instant + proc_comp

# print(system_decls)
sys.system = u.SystemDeclaration(system_decls)
# save the system to xml
sys.to_file(path='UPPAAL-Stratego/bin-Windows/simulator_output.xml', pretty=True)

# Write the query file
query_file = open('UPPAAL-Stratego/bin-Windows/query.q', 'w')
query = "simulate " + str(simulations) + " [<= 1000] {"
for i in range(nodes):
    if i > 0:
        query += ", "
    query += "c" + str(i)
query += "}"
query_file.write(query)
query_file.close()

os.chdir('UPPAAL-Stratego/bin-Windows')
cmd = 'verifyta simulator_output.xml query.q'
with open('simulations.txt', 'w') as out:
    return_code = subprocess.call(cmd, stdout=out)

# Call the trace converter
os.chdir('..')
os.chdir('..')
os.system('python converter.py ' + str(nodes) + " " + str(simulations) + " " + 'UPPAAL-Stratego/bin-Windows/simulations.txt')
