# SPDX-License-Identifier: GPL-3
# Copyright (c) 2022: Ludwig Schneider
# See LICENSE for details

import copy
from warnings import warn

from .core import BigSMILESbase
from .mixture import Mixture
from .molecule import Molecule


def _estimate_system_molecular_weight(molecules, system_molweight):
    estimated_weights = []
    if system_molweight:
        estimated_weights.append(system_molweight)
    num_fractions = 0
    total_fraction = 0
    total_mass = 0
    num_mass = 0

    for i in range(len(molecules)):
        mol = molecules[i]
        if mol.mixture is not None:
            if mol.mixture.absolute_mass:
                total_mass += mol.mixture.absolute_mass
                num_mass += 1
            if mol.mixture.relative_mass is not None:
                total_fraction += mol.mixture.relative_mass
                num_fractions += 1

    if num_fractions == len(molecules) - 1:
        weight = 100.0 - total_fraction
        if weight < 0 or weight > 100.0:
            raise RuntimeError(
                f"Unable to adjust weight for system. {weight} Invalid extra weight."
            )
        total_fraction += weight
        num_fractions += 1
        for mol in molecules:
            if mol.mixture is None:
                mol.mixture = Mixture(f".|{weight}%|")
            if mol.mixture.relative_mass is None:
                mol.mixture.relative_mass = weight

    if num_fractions == len(molecules) and abs(total_fraction - 100) > 1e-6:
        raise RuntimeError(
            f"Error adjusting system fractional weight. Total fraction {total_fraction} invalid != 100."
        )

    for mol in molecules:
        if mol.mixture and mol.mixture.system_mass:
            estimated_weights.append(mol.mixture.system_mass)

    if num_mass == len(molecules):
        estimated_weights.append(total_mass)

    if len(estimated_weights) > 1:
        for i in range(len(estimated_weights) - 1):
            if abs(estimated_weights[i] - estimated_weights[i + 1]) > 1e-6:
                raise RuntimeError(
                    f"System described with inconsistent mol weights {estimated_weights}."
                )

    try:
        system_weight = estimated_weights[0]
    except IndexError:
        warn(
            "The system cannot be generated, since the total system molecular weight cannot be estimated."
        )
        return False
    for mol in molecules:
        if mol.mixture is None:
            warn(
                "The system cannot be generated, since at least one weight is underspecified even as total mass is known."
            )
            return False
        mol.mixture.system_mass = system_weight

    return True


class System(BigSMILESbase):
    """
    Entire system representation in extended bigSMILES.
    """

    def __init__(self, big_smiles_ext, system_molweight=None):
        """
        Construction of an entire system (mixtures).

        Arguments:
        ----------
        big_smiles_ext: str
           text representation
        """
        self._raw_text = big_smiles_ext.strip()

        self._molecules = []
        text = copy.copy(self._raw_text)
        while text.find(".|") >= 0:
            # text = text[text.find(".|") :].strip()
            end_pos = text.find("|", text.find(".|") + 2) + 1
            if end_pos < 0:
                raise RuntimeError(
                    f"System {text} contains an opening '.|' for a stochastic object, but no closing '|'."
                )
            self._molecules.append(Molecule(text[:end_pos]))
            text = text[end_pos:].strip()

        if len(text) > 0:
            mol = Molecule(text)
            self._molecules.append(mol)

        self._generable = _estimate_system_molecular_weight(self._molecules, system_molweight)

    @property
    def generable(self):
        if not self._generable:
            return False
        for mol in self._molecules:
            if not mol.generable:
                return False
        return True

    def generate_string(self, extension):
        string = ""
        for mol in self._molecules:
            string += mol.generate_string(extension)

        return string
