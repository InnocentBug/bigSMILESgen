#!/usr/bin/env python

# import matplotlib.pyplot as plt

# import pydot
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

import bigsmiles_gen


def test_mirror(bigA):
    molA = bigsmiles_gen.Molecule(bigA)
    print(bigA)
    print(molA)
    print(molA.generate().smiles)
    molB = molA.gen_mirror()
    print(molB)
    print(molB.generate().smiles)


def test_prob(bigA):
    mol = bigsmiles_gen.Molecule(bigA)
    smi = mol.generate().smiles
    print(bigA)
    print(smi)
    prob, matches = bigsmiles_gen.mol_prob.get_ensemble_prob(smi, mol)
    print(prob)
    print(matches)


bigA = "{[][<]C(N)C[>]; [<][H][>]}|uniform(500, 600)|{[<][<]C(=O)C[>]; [>][H][]}|uniform(500, 600)|"
bigA = "CCO{[<][<]C(N)C[>][>]}|uniform(500, 600)|{[<][<]C(=O)C[>][>]}|uniform(500, 600)|CCN"
# test_mirror(bigA)
# bigA = "CCO"
# test_prob(bigA)
bigA = "{[][<]C(N)C[>]; [<][H], [>]CO []}|uniform(560, 600)|"
# test_prob(bigA)

bigA = "{[] CC([<])=NCC[>], [$2]CC(=O)C([<])CC[$2]; [F][>], CCO[<], [H][$2][]}|uniform(100, 150)|"
bigA = "OCC{[$] [$]C(N)C[$], [$]CC(C(=O)C[$2])C[$], [$2]CCC[$2] ;[H][$], [Si][$2] [$]}|gauss(500, 10)|CCN"
bigA = "OC{[>] [<]CC[>], [<|.5|]C(N[>|.1 0 0 0 0 0 0|])C[>]; [<][H], [<]C [<]}|schulz_zimm(750, 600)|COOC{[<] [<]COC[>], [<]C(ON)C[>] [>]}|schulz_zimm(200, 150)|{[<] [<]COCOC[>], [<]CONOC[>] [>]}|schulz_zimm(170, 150)|F"
bigA = "OC{[<] [<]CC[>], [<|.5|]C(N[>|.1 0 0 0 0 0|])C[>]; [<][H] [>]}|schulz_zimm(750, 600)|C=O.|5000|"

bigA = "[H]{[<] [<]CC([>])c1ccccc1 [>]}|schulz_zimm(2000, 1800)|{[<] [<]CC([>])(C)C(=O)OC [>]}|schulz_zimm(2000, 1800)|[H]"

mol = bigsmiles_gen.Molecule(bigA)
mol_gen = mol.generate()
print(mol_gen.smiles)
molSize = (450, 150)
mc = Chem.Mol(mol_gen.mol.ToBinary())
drawer = rdMolDraw2D.MolDraw2DSVG(molSize[0], molSize[1])
drawer.DrawMolecule(mc)
drawer.FinishDrawing()
svg = drawer.GetDrawingText()
with open("molPlay.svg", "w") as filehandle:
    filehandle.write(svg)

print(mol.generate_string(True))
graph = mol.gen_reaction_graph()
graph_dot = bigsmiles_gen.reaction_graph_to_dot_string(graph, mol)

with open("graph.dot", "w") as filehandle:
    filehandle.write(graph_dot)


# for i in range(100):
#     smi = mol.generate().smiles
#     print(smi)
#     # print(bigsmiles_gen.mol_prob.get_ensemble_prob(smi, mol)[0])
