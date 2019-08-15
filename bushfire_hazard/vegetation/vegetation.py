"""
Generic vegetation definition.

Define an abstract vegetation class. Based on the paper:

Midgley, S. & Tan, Z., 2006. A methodology for determining minimum separation
distance between a structure and bushfire hazard. Life In A Fire-Prone
Environment: Translating Science Into Practice, pp.6–9.

this defines the standard methods as required to determine the flame length,
rate of spread, radiant heat flux, view factor and transmittance factor.
"""
import abc

from memoize import Memoizer
import numpy as np
from scipy.optimize import minimize_scalar


store = {}
memo = Memoizer(store)


class Vegetation(abc.ABC):
    """Abstract class of vegetation"""

    heat_of_combustion = 18600  # kJ/kg
    flame_emissivity = 0.95
    sigma = 5.67 * 10**-11  # kW/m^2K^4
    flame_temperature = 1200  # K
    flame_width = 100  # m
    ambient_temperature = 308  # K
    relative_humidity = 0.25

    def __init__(self, site_slope, receiver_height):
        """Required parameters for simulation on a per site basis

        :param site_slope: slope between flame and receiver in radians
        :param receiver_height: height of receiver in metres
        """
        self.site_slope = site_slope
        self.receiver_height = receiver_height

    @abc.abstractmethod
    def _flame_length(self):
        """Flame length calculations based on Table 1"""
        pass

    @property
    @memo
    def flame_length(self):
        return self._flame_length()

    @abc.abstractmethod
    def _rate_of_spread(self):
        """Rate of spread calculations as per Table 2"""
        pass

    @property
    @memo
    def rate_of_spread(self):
        return self._rate_of_spread()

    def radiant_heat_flux(self, separation_distance):
        r"""Radiant heat flux as outlined on page 4

        Radiant heat flux is calculated as:

        $$ R_d = \phi \epsilon \sigma T^4 \tau$$

        Where

        - $R_d$ is radiant heat flux ($kW/m^2$)
        - $\phi$ is view factor
        - $\epsilon$ is flame emissivity, defaulted to 0.95
        - $\sigma$ is $5.67 \times 10^{-11} kW/m^2K^4$
        - $T$ is flame temperature, defaulted to 1200K
        - $\tau$ is transmittance factor

        :param separation_distance: horizontal distance from flame to receiver, in metres
        :rtype: float
        """

        @np.vectorize
        def radiant_heat(separation_distance):
            """Purely here to make the vectorization easy"""
            phi, angle = self.view_factor(separation_distance)
            tau = self.transmittance_factor(angle, separation_distance)

            return (
                    phi                            # phi
                    * self.flame_emissivity        # epsilon
                    * self.sigma                   # sigma
                    * self.flame_temperature**4    # T**4
                    * tau                          # tau
            )

        return radiant_heat(separation_distance)

    def _view_factor_calc(self, angle, separation_distance):
        """Given a single view angle return the view factor

        :param separation_distance: horizontal distance from flame to receiver, in metres
        :rtype: float
        """
        path_length = separation_distance - 0.5 * self.flame_length * np.cos(angle)
        x_1 = (
            (self.flame_length * np.sin(angle) - 0.5 * self.flame_length * np.cos(angle) * np.tan(self.site_slope) - separation_distance * np.tan(self.site_slope) - self.receiver_height) /
            path_length
        )
        x_2 = (
            (
                self.receiver_height +
                path_length *
                np.tan(self.site_slope)
            ) /
            path_length
        )
        y_1 = (
            (0.5 * self.flame_width) /
            path_length
        )
        y_2 = (
            (0.5 * self.flame_width) /
            path_length
        )
        phi = 1 / np.pi * (
            x_1 / np.sqrt(1 + x_1**2) * np.arctan(y_1 / np.sqrt(1 + x_1**2)) +
            y_1 / np.sqrt(1 + y_1**2) * np.arctan(x_1 / np.sqrt(1 + y_1**2)) +
            x_2 / np.sqrt(1 + x_2**2) * np.arctan(y_2 / np.sqrt(1 + x_2**2)) +
            y_2 / np.sqrt(1 + y_2**2) * np.arctan(x_2 / np.sqrt(1 + y_2**2))
        )
        return phi

    def view_factor(self, separation_distance):
        """View factor as outlined on page 5

        As per the paper the view factor requires five parameters:

        1. flame length
        2. flame width, defaulted as 100m
        3. flame angle
        4. elevation of receiver
        5. site slope

        Flame length is determined based on vegetation and modelling conditions,
        and elevation of the receiver and the site slope are site specific. As
        such there exists a flame angle which gives the maximum value for the
        view factor - thus this is a numeric optimisation problem.

        :param separation_distance: horizontal distance from flame to receiver, in metres
        :return: the view factor and the angle for that view factor
        :rtype: float, float
        """
        res = minimize_scalar(
            lambda angle: - self._view_factor_calc(angle, separation_distance),
            bounds=(0, np.pi),
            method='bounded'
        )
        return -res.fun, res.x  # negative of the objective function

    _calculation_coefficients = np.array([
        [1.486, -2.003e-3, 4.68e-5, -6.052e-2],
        [1.225e-2, -5.900e-5, 1.66e-6, -1.759e-3],
        [-1.489e-4, 6.893e-7, -1.922e-8, 2.092e-5],
        [8.381e-7, -3.283e-9, 1.051e-10, -1.166e-7],
        [-1.685e-9, 7.637e-12, -2.085e-13, 2.350e-10],
    ])

    def transmittance_factor(self, angle, separation_distance):
        """Transmittance factor as outlined on page 6

        Happily we can use numpy broadcasting to calculate this easily.

        :param angle: The angle of the flame determined for the maximum view factor
        :param separation_distance: horizontal distance from flame to receiver, in metres
        :rtype: float
        """
        a_n_coefficients = np.array([
            1,
            self.ambient_temperature,
            self.flame_temperature,
            self.relative_humidity
        ])
        a_n = (a_n_coefficients * self._calculation_coefficients).sum(axis=1)

        path_length = separation_distance - 0.5 * self.flame_length * np.cos(angle)

        path_length_powers = path_length ** np.arange(5)

        tau = (a_n * path_length_powers).sum()

        return tau
