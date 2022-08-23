# SPDX-License-Identifier: GPL-3
# Copyright (c) 2022: Ludwig Schneider
# See LICENSE for details

from warnings import warn

from .core import BigSMILESbase


class Mixture(BigSMILESbase):
    """
    Class to describe mixtures of systems.
    Systems with one component are considered a mixture too.
    """

    def __init__(self, raw_text):
        """
        Initialize the mixture description.

        Arguments:
        ----------
        raw_text: str
             Text represenation of the distribution. Example: `.|1234.|` or `.|30%|`
        """
        self._raw_text = raw_text

        if self._raw_text[0] != ".":
            raise RuntimeError(
                f"Mixture descriptions start with '.', but it is missing in {self._raw_text}"
            )
        self._absolute_mass = None
        self._relative_mass = None
        self._system_mass = None
        if "%" in self._raw_text:
            rel_mass = float(self._raw_text.strip(".|%"))
            if rel_mass < 0 or rel_mass > 100:
                raise RuntimeError(f"Mixture relative mass invalid percent {self._raw_text}.")
            self._relative_mass = rel_mass
            print(rel_mass, self._relative_mass)
        else:
            try:
                abs_mass = float(self._raw_text.strip(".|"))
            except ValueError:
                warn(
                    f"Mixture descriptor {self._raw_text} does not specify a valid mixture, the system will not be generatable."
                )
            else:
                if abs_mass < 0:
                    raise RuntimeError(f"Mixture absolute mass invalid {self._raw_text}.")
                self._absolute_mass = abs_mass

    @property
    def absolute_mass(self):
        return self._absolute_mass

    @property
    def relative_mass(self):
        return self._relative_mass

    @property
    def system_mass(self):
        return self._system_mass

    @system_mass.setter
    def system_mass(self, mass):
        if mass < 0:
            raise RuntimeError(f"Invalid negative total system mass {mass}.")
        self._system_mass = mass
        if self._relative_mass is not None:
            self._absolute_mass = self._relative_mass / 100.0 * mass
            return

        if self._absolute_mass is not None:
            self._relative_mass = 100 * self._absolute_mass / mass
            return

    def pure_big_smiles(self):
        return "."

    def __str__(self):
        if self.absolute_mass is None:
            print(self.relative_mass)
            return f".|{self.relative_mass}%|"
        return f".|{self.absolute_mass}|"

    @property
    def generatable(self):
        return self.absolute_mass is not None
