import networkx as nx
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem

from .distribution import SchulzZimm
from .molecule import Molecule
from .stochastic import Stochastic
from .token import SmilesToken

STATIC_BOND_WEIGHT = -1


def _generate_stochastic_atom_graph(molecule: Molecule, distribution: bool = True):
    if distribution and not molecule.generable:
        raise RuntimeError("G-BigSMILES Molecule must be generable for a stochastic atom graph.")

    # Check distribution possibility
    for element in molecule.elements:
        if isinstance(elements, Stochastic):
            if not isinstance(elements.distribution, SchulzZimm):
                raise RuntimeError(
                    "At the moment, we only support SchulzZimm Distribution for stochastic atom graphs."
                )

    graph = nx.MultiDiGraph()
    node_counter = 0
    node_offset_list = [[0]]
    # Add all nodes and static weights
    for element in molecule.elements:
        if isinstance(element, SmilesToken):
            smi = element.generate_smiles_fragment()
            mol = Chem.MolFromSmiles(smi)
            mw_info = (Chem.Descriptors.HeavyAtomMolWt(mol), Chem.Descriptors.HeavyAtomMolWt(mol))
            nodes = _get_token_nodes(element, mw_info, distribution)

            graph = _add_nodes_to_graph(graph, nodes, node_counter)

            node_counter += len(nodes)
            node_offset_list.append([node_counter + len(nodes)])

        if isinstance(element, Stochastic):
            mw_info = (distribution._Mn, distribution._Mw)
            nested_offset = [node_counter]
            for token in element.repeat_tokens:
                nodes = _get_token_nodes(token, mw_info, distribution)
                graph = _add_nodes_to_graph(graph, nodes, node_counter)
                node_counter += len(nodes)
                nested_offset.append(nested_offset[-1] + len(nodes))
            for token in element.end_tokens:
                nodes = _get_token_nodes(token, mw_info, distribution)
                graph = _add_nodes_to_graph(graph, nodes, node_counter)
                node_counter += len(nodes)
                nested_offset.append(nested_offset[-1] + len(nodes))

            # Add stochastic bonds inside the stochastic element
            for graph_bd in element.bond_descriptors:
                graph_bd_token_idx = _find_bd_token(element, graph_bd)
                # Add regular weights for listed bd
                if graph_bd.transitions is not None:
                    prob = graph_bd.transitions
                    for i, p in enumerate(prob):
                        other_bd = element.bond_descriptors[i]
                        other_bd_token_idx = _find_bd_token(element, other_bd)
                        if p > 0:
                            first_atom = (
                                graph_bd.atom_bonding_to + nested_offset[graph_bd_token_idx]
                            )
                            second_atom = (
                                other_bd.atom_bonding_to + nested_offset[other_bd_token_idx]
                            )
                            graph.add_edge(
                                first_atom,
                                second_atom,
                                bond_type=int(graph_bd.bond_type),
                                weight=p,
                                termination_weight=graph_bd.weight,
                                transition_weight=0,
                            )
                else:
                    for other_bd in element.bond_descriptors:
                        if graph_bd.is_compatible(other_bd) and other_bd.weight > 0:
                            other_bd_token_idx = _find_bd_token(element, other_bd)
                            first_atom = (
                                graph_bd.atom_bonding_to + nested_offset[graph_bd_token_idx - 1]
                            )
                            second_atom = (
                                other_bd.atom_bonding_to + nested_offset[other_bd_token_idx - 1]
                            )

                            if other_bd_token_idx < len(element.repeat_tokens):
                                graph.add_edge(
                                    first_atom,
                                    second_atom,
                                    bond_type=int(graph_bd.bond_type),
                                    weight=other_bd.weight,
                                    termination_weight=0,
                                    transition_weight=0,
                                )
                            else:
                                graph.add_edge(
                                    first_atom,
                                    second_atom,
                                    bond_type=int(graph_bd.bond_type),
                                    termination_weight=other_bd.weight,
                                    weight=0,
                                )

                node_offset_list.append(nested_offset)

    # Add transitions between elements, this is the first
    for element_lhs_i, element_lhs in enumerate(molecule.elements[:-1]):
        element_rhs_i = element_lhs_i + 1
        element_rhs = molecule.elements[element_rhs_i]
        for bd_lhs in element_lhs.bond_descriptors:
            for bd_rhs in element_rhs.bond_descriptors:
                if bd_lhs.is_compatible(bd_rhs):
                    terminal_ok = False
                    try:
                        terminal_ok = bd_lhs.is_compatible(element_rhs.left_terminal)
                    except AttributeError:
                        if isinstance(element_rhs, SmilesToken):
                            terminal_ok = True
                    if terminal_ok:
                        bd_lhs_idx = _find_bd_token(element_lhs, bd_lhs)
                        bd_rhs_idx = _find_bd_token(element_rhs, bd_rhs)
                        first_atom = (
                            node_offset_list[element_lhs_i][bd_lhs_idx] + bd_lhs.atom_bonding_to
                        )
                        second_atom = (
                            node_offset_list[element_rhs_i][bd_rhs_idx] + bd_rhs.atom_bonding_to
                        )
                        graph.add_edge(
                            first_atom,
                            second_atom,
                            bond_type=int(bd_lhs.bond_type),
                            termination_weight=0,
                            weight=0,
                            transition_weight=bd_rhs.weight,
                        )

    return graph


def _find_bd_token(element, bd):
    try:
        for i, token in enumerate(element.repeat_tokens):
            if bd in token.bond_descriptors:
                return i
        for i, token in enumerate(element.end_tokens):
            if bd in token.bond_descriptors:
                return i + len(element.repeat_tokens)
    except AttributeError:
        if isinstance(element, SmilesToken):
            return 0


def _add_nodes_to_graph(graph, nodes, node_counter):
    for node in nodes:
        atom = node["atom"]
        mw_info = node["mw_info"]

        graph.add_node(
            node_counter + atom.GetIdx(),
            atomic_num=atom.GetAtomicNum(),
            valence=atom.GetTotalValence(),
            formal_charge=atom.GetFormalCharge(),
            aromatic=atom.GetIsAromatic(),
            hybridization=int(atom.GetHybridization()),
            mn=mw_info[0],
            mw=mw_info[1],
        )
    for node in nodes:
        atom = node["atom"]
        static_bonds = node["static_bonds"]
        for other_idx in static_bonds:
            bond_a = atom.GetIdx() + node_counter
            bond_b = other_idx + node_counter
            graph.add_edge(
                bond_a,
                bond_b,
                bond_type=int(static_bonds[other_idx].GetBondType()),
                weight=STATIC_BOND_WEIGHT,
                termination_weight=0,
                transition_weight=0,
            )

    return graph


def _get_token_nodes(token: SmilesToken, mw_info, distribution: bool):
    smi = token.generate_smiles_fragment()
    mol = Chem.MolFromSmiles(smi)
    mol = Chem.AddHs(mol)

    mol = _remove_extra_hydrogen_atoms(token, mol)

    nodes = []
    for atom_idx in range(mol.GetNumAtoms()):
        atom = mol.GetAtomWithIdx(atom_idx)

        static_bonds = {}
        for bond in atom.GetBonds():
            if bond.GetBeginAtomIdx() == atom_idx:
                other_atom_idx = bond.GetEndAtomIdx()
            if bond.GetEndAtomIdx() == atom_idx:
                other_atom_idx = bond.GetBeginAtomIdx()
            static_bonds[other_atom_idx] = bond

        node_properties = {"atom": atom, "static_bonds": static_bonds}
        if distribution:
            node_properties["mw_info"] = mw_info

    return nodes


def _remove_extra_hydrogen_atoms(token, mol):
    # Quick exit for single atom tokens:
    if mol.GetNumAtoms() == 1:
        return mol
    # We need to remove hydrogens, where we have a bond descriptor connected to.
    atoms_to_be_deleted = []
    for bd in token.bond_descriptors:
        origin_atom_idx = bd.atom_bonding_to
        origin_atom = mol.GetAtomWithIdx(origin_atom_idx)
        for bond in origin_atom.GetBonds():
            if bond.GetBeginAtomIdx() == origin_atom_idx:
                other_atom_idx = bond.GetEndAtomIdx()
            if bond.GetEndAtomIdx() == origin_atom_idx:
                other_atom_idx = bond.GetBeginAtomIdx()

            if other_atom_idx not in atoms_to_be_deleted:
                # We can't remove atoms twice (shouldn't happen anyways)
                other_atom = mol.GetAtomWithIdx(other_atom_idx)

                # Make sure we remove a hydrogen
                if other_atom.GetAtomicNum() == 1:
                    atoms_to_be_deleted += [other_atom_idx]
                    # Exit from the bond loop, since we only delete one atom
                    break

    atoms_to_be_deleted = sorted(atoms_to_be_deleted)
    edit_mol = Chem.EditableMol(mol)
    for i, atom_idx in enumerate(atoms_to_be_deleted):
        edit_mol.RemoveAtom(atom_idx - i)
    mol = edit_mol.GetMol()
    Chem.SanitizeMol(mol)

    return mol
