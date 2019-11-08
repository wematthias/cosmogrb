import numpy as np
import scipy.integrate as integrate
import numba as nb

from .sampler import Sampler


@nb.jit(forceobj=True)
def source_poisson_generator(tstart, tstop, function, fmax):
    """
    Non-homogeneous poisson process generator
    for a given max rate and time range, this function
    generates time tags sampled from the energy integrated
    lightcurve.
    """
    time = tstart

    arrival_times = [tstart]

    while time < tstop:

        time = time - (1.0 / fmax) * np.log(np.random.rand())
        test = np.random.rand()

        p_test = function(time) / fmax

        if test <= p_test:
            arrival_times.append(time)

    return np.array(arrival_times)


@nb.jit(forceobj=True)
def evolution_sampler(times, N, function, grid, emin, emax):

    out = np.zeros(N)

    for i, t in enumerate(times):

        flag = True

        # find the maximum of the function.
        fmax = np.max(function(grid, np.array([t]))[0, :])

        while flag:

            test = np.random.uniform(0, fmax)
            x = np.random.uniform(emin, emax)

            if test <= function(np.array([x]), np.array([t]))[0, 0]:

                out[i] = x
                flag = False

    return out


@nb.jit()
def plaw_evolution_sampler(times, N, function, index, emin, emax):
    """
    specialized sample for power law like functions for 
    increased speed


    :param times: 
    :param N: 
    :param function: 
    :param index: 
    :param emin: 
    :param emax: 
    :returns: 
    :rtype: 

    """

    out = np.zeros(N)

    for i in range(N):

        flag = True

        C = function(emin, times[i])[0, 0]

        while flag:

            # sample from a power law
            u = np.random.uniform(0, 1)
            x = np.power(
                (np.power(emax, index + 1) - np.power(emin, index + 1)) * u
                + np.power(emin, index + 1),
                1.0 / (index + 1.0),
            )

            y = np.random.uniform(0, 1) * C * np.power(x, index)

            if y <= function(x, times[i])[0, 0]:

                out[i] = x
                flag = False

    return out


class SourceFunction(object):
    def __init__(self, emin=10.0, emax=1.0e4, index=None):
        """
        The source function in time an energy

        :returns: 
        :rtype: 

        """

        self._index = index
        self._emin = emin
        self._emax = emax

    def evolution(self, energy, time):

        raise NotImplementedError()

    def energy_integrated_evolution(self, time):
        """
        return the integral over energy at a given time 
        via Simpson's rule

        :param time: the time of the pulse

        :returns: 
        :rtype: 

        """

        ene_grid = np.logspace(np.log10(self._emin), np.log10(self._emax), 11)

        return integrate.simps(self.evolution(ene_grid, time)[0, :], ene_grid)

    @property
    def index(self):
        return self._index

    @property
    def emin(self):
        return self._emin

    @property
    def emax(self):
        return self._emax


class Source(Sampler):
    def __init__(self, tstart, tstop, source_function, use_plaw_sample=False):

        self._source_function = source_function

        self._use_plaw_sample = use_plaw_sample

        self._energy_grid = np.logspace(
            np.log10(self._source_function.emin),
            np.log10(self._source_function.emax),
            25,
        )

        # pass on tstart and tstop

        super(Source, self).__init__(tstart=tstart, tstop=tstop)

        # precompute fmax by integrating over energy

        self._fmax = self._get_energy_integrated_max()

    def _get_energy_integrated_max(self):
        """
        return the maximum flux in photon number integrated over the energy
        range

        :param start: 
        :param stop: 
        :returns: 
        :rtype: 

        """

        # need to find the energy integrated peak flux
        num_grid_points = 50

        time_grid = np.linspace(self._tstart, self._tstop, num_grid_points)

        fluxes = [
            self._source_function.energy_integrated_evolution(t) for t in time_grid
        ]

        return np.max(fluxes)

    def sample_times(self):
        """
        sample the evolution function INTEGRATED
        over energy

        :returns: 
        :rtype: 

        """

        return source_poisson_generator(
            self._tstart,
            self._tstop,
            self._source_function.energy_integrated_evolution,
            self._fmax,
        )

    def sample_photons(self, times):

        if not self._use_plaw_sample:

            return evolution_sampler(
                times,
                len(times),
                self._source_function.evolution,
                self._energy_grid,
                self._source_function.emin,
                self._source_function.emax,
            )

        else:

            return plaw_evolution_sampler(
                times,
                len(times),
                self._source_function.evolution,
                self._source_function.index,
                self._source_function.emin,
                self._source_function.emax,
            )

    def sample_channel(self, photons, response):

        channel, detect = response.digitize(photons)

        return channel, detect