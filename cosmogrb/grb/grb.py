import h5py
import multiprocessing as mp
import  collections
import coloredlogs, logging


from cosmogrb.sampler.source import Source
from cosmogrb.sampler.background import Background
import cosmogrb.utils.logging
logger = logging.getLogger("cosmogrb.grb")



class GRB(object):
    def __init__(self, name="SynthGRB", source_class, background_class,  duration=1,  z=1, T0=0, ra=0, dec=0, source_params={}, background_params = {}):
        """
        A basic GRB

        :param name: 
        :param verbose: 
        :returns: 
        :rtype: 

        """
        self._name = name
        self._T0 = T0
        self._duration = duration
        self._z = z
        self._ra = ra
        self.dec = dec
        self._source_class = source_class
        self._background_class = background_class
        

        assert z > 0, f'z: {z} must be greater than zero'
        assert duration > 0, f'duration: {duration} must be greater than zero'
        assert issubclass(source_class, Source)
        assert issubclass(background_class, Background)

        self._source_params = source_params
        self._background_params = background_params
        
        logger.debug(f"created a GRB with name: {name}")
        logger.debug(f"created a GRB with ra: {ra} and dec: {dec}")
        logger.debug(f"created a GRB with redshift: {z}")
        logger.debug(f"created a GRB with duration: {duration} and T0: {T0}")

        # create an empty list for the light curves
        # eetc
        self._lightcurves = collections.OrderedDict()
        self._responses = collections.OrderedDict()
        self._backgrounds = collections.OrderedDict()

    def _setup(self):

        assert len(self._responses) > 0

        for key in self._responses.keys():

            

    def _add_background(self, name, background):

        self._backgrounds[name] = background
        
    def _add_response(self, name, response):

        self._responses[name] = response

        logger.debug(f"Added response: {name}")
        
    def _add_lightcurve(self, lightcurve):
        """
        add a light curve to the GRB. This is really just adding 
        a detector on

        :param lightcurve: 
        :returns: 
        :rtype: 

        """

        self._lightcurves[lightcurve.name] = lightcurve

        logger.debug(f"Added lightcuve: {lightcurve.name}")

    def go(self, n_cores=8):

        pool = mp.Pool(n_cores)

        pool.map(process_lightcurve, self._lightcurves.values())
        pool.close()
        pool.join()

    def save(self, file_name):
        """
        save the grb to an HDF5 file


        :param file_name: 
        :returns: 
        :rtype: 

        """

        with h5py.File(file_name, "w") as f:

            # save the general
            f.attrs["grb_name"] = self._name
            f.attrs["n_lightcurves"] = len(self._lightcurves)
            f.attrs['T0'] = self._T0
            det_group = f.create_group("detectors")

            for lightcurve in self._lightcurves:

                lc = lightcurve.lightcurve_storage

                lc_group = det_group.create_group(f"{lc.name}")

                lc_group.create_dataset("channels", data=lc.channels)

                # now create groups for the total, source and bkg
                # counts

                total_group = lc_group.create_group("total_signal")

                total_group.create_dataset("pha", data=lc.pha)
                total_group.create_dataset("times", data=lc.times)

                source_group = lc_group.create_group("source_signal")

                source_group.create_dataset("pha", data=lc.pha_source)
                source_group.create_dataset("times", data=lc.times_source)

 3               source_group = lc_group.create_group("background_signal")

                source_group.create_dataset("pha", data=lc.pha_source)
                source_group.create_dataset("times", data=lc.times_source)

                rsp_group = lc_group.create_group("response")

                rsp_group.create_dataset("matrix", data=lightcurve.response.matrix)
                rsp_group.create_dataset(
                    "enegy_edges", data=lightcurve.response.energy_edges
                )
                rsp_group.create_dataset(
                    "channel_edges", data=lightcurve.response.channel_edges
                )
                rsp_group.attrs["geometric_area"] = lightcurve.response.geometric_area

    def display_energy_dependent_light_curve(
        self, time, energy, ax=None, cmap="viridis", **kwargs
    ):
        """FIXME! briefly describe function

        :param time: 
        :param energy: 
        :param ax: 
        :param cmap: 
        :returns: 
        :rtype: 

        """

        self._lightcurves[0].display_energy_dependent_light_curve(
            time=time, energy=energy, ax=ax, cmap=cmap, **kwargs
        )

    def display_energy_integrated_light_curve(self, time, ax=None, **kwargs):
        """FIXME! briefly describe function

        :param time: 
        :param ax: 
        :returns: 
        :rtype: 

        """

        self._lightcurves[0].display_energy_integrated_light_curve(
            time=time, ax=ax, **kwargs
        )


def process_lightcurve(lc):
    lc.process()
