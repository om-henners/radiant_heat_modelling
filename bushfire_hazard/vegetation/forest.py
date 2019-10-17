"""
Specific calculations for forest types
"""
import abc

import numpy as np

from .vegetation import Vegetation


class ForestWoodland(Vegetation):
    """Specific flame length calculations for forest and woodland"""

    @property
    @abc.abstractmethod
    def overall_fuel_load(self):
        pass

    @property
    @abc.abstractmethod
    def surface_fuel_load(self):
        pass

    def __init__(self, site_slope, receiver_height, fdi):
        self.fdi = fdi
        super().__init__(site_slope, receiver_height)

    def _flame_length(self):
        """Flame length calculations based on Table 1.

        Flame length for forests and woodlands is defined as:

        $$ L_f =(13R +0.24W)/2 $$

        Where

        - $L_f$ is the flame length
        - $R$ is the rate of spread
        - $W$ is the overall fuel load

        :rtype: float
        """
        return (13 * self.rate_of_spread + 0.24 * self.overall_fuel_load) / 2

    def _rate_of_spread(self):
        """Rate of spread calculations as per Table 2

        :rtype: float
        """
        return 0.0012 * self.fdi * self.surface_fuel_load * np.exp(0.069 * self.site_slope)


class Forest(ForestWoodland):
    """Specific type based on Table 3"""

    @property
    def overall_fuel_load(self):
        return 35  # t/ha

    @property
    def surface_fuel_load(self):
        return 25


class Woodland(ForestWoodland):
    """Specific type based on Table 3"""

    @property
    def overall_fuel_load(self):
        return 25  # t/ha

    @property
    def surface_fuel_load(self):
        return 15
