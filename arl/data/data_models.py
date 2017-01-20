# Tim Cornwell <realtimcornwell@gmail.com>
""" Data models used in ARL"""

import logging
import sys

import numpy
from astropy import units as u
from astropy.constants import c
from astropy.coordinates import SkyCoord
from astropy.table import Table

log = logging.getLogger(__name__)


class Configuration:
    """ Describe a Configuration
    
    Has a Table with locations in x,y,z, and names, and overall location
    """
    
    def __init__(self, name='', data=None, location=None,
                 names="%s", xyz=None, mount="alt-az"):
        
        # Defaults
        if data is None and not xyz is None:
            nants = xyz.shape[0]
            if isinstance(names, str):
                names = [names % ant for ant in range(nants)]
            if isinstance(mount, str):
                mount = numpy.repeat(mount, nants)
            data = Table([names, xyz, mount],
                         names=['names', 'xyz', 'mount'])
        
        self.name = name
        self.data = data
        self.location = location
    
    def __sizeof__(self):
        """ Return size in GB
        """
        size = 0
        for col in self.data.colnames:
            size += self.data[col].size * sys.getsizeof(self.data[col])
        return size / 1024.0 / 1024.0 / 1024.0
    
    @property
    def names(self):
        """ Names of the antennas/stations"""
        return self.data['names']
    
    @property
    def xyz(self):
        """ XYZ locations of antennas/stations
        """
        return self.data['xyz']
    
    @property
    def mount(self):
        """ Mount type
        """
        return self.data['mount']


class GainTable:
    """ Gain table with data: time, antenna, gain[:,chan,pol] columns
    """
    
    # TODO: Implement gaintables with Jones and Mueller matrices
    
    def __init__(self):
        self.data = None
        self.frequency = None


class Image:
    """Image class with Image data (as a numpy.array) and optionally the AstroPy WCS.

    Many operations can be done conveniently using numpy arl on Image.data.

    Most of the imaging arl require an image in canonical format:
    - 4 axes: RA, DEC, POL, FREQ

    The conventions for indexing in WCS and numpy are opposite.
    - In astropy.wcs, the order is (longitude, latitude, polarisation, frequency)
    - in numpy, the order is (frequency, polarisation, latitude, longitude)

    """
    
    def __init__(self):
        """ Empty image
        """
        self.data = None
        self.wcs = None
    
    def __sizeof__(self):
        """ Return size in GB
        """
        size = 0
        size += self.data.size * sys.getsizeof(self.data.dtype)
        return size / 1024.0 / 1024.0 / 1024.0
    
    @property
    def nchan(self): return self.data.shape[0]
    
    @property
    def npol(self): return self.data.shape[1]
    
    @property
    def npixel(self): return self.data.shape[3]
    
    @property
    def frequency(self):
        # Extracted from find_skycomponent. Not sure how generally
        # applicable this is.
        w = self.wcs.sub(['spectral'])
        return w.wcs_pix2world(range(self.nchan), 1)[0]
    
    @property
    def shape(self):
        return self.data.shape
    
    @property
    def phasecentre(self): return SkyCoord(self.wcs.wcs.crval[0] * u.deg, self.wcs.wcs.crval[1] * u.deg)
    
    def __exit__(self):
        log.debug("Image:Exiting from image of shape: %s" % (self.data.shape))


class Skycomponent:
    """ A single Skycomponent with direction, flux, shape, and params for the shape
    
    """
    
    def __init__(self,
                 direction=None, frequency=None, name=None, flux=None, shape='Point', **kwargs):
        """ Define the required structure

        :param direction: SkyCoord
        :param frequency: numpy.array [nchan]
        :param name: user friendly name
        :param flux: numpy.array [nchan, npol]
        :param shape: str e.g. 'Point' 'Gaussian'
        :param params: numpy.array shape dependent parameters
        """
        
        self.direction = direction
        self.frequency = numpy.array(frequency)
        self.name = name
        self.flux = numpy.array(flux)
        self.shape = shape
        self.params = kwargs
        
        assert len(self.frequency.shape) == 1
        assert len(self.flux.shape) == 2
        assert self.frequency.shape[0] == self.flux.shape[0], "Frequency shape %s, flux shape %s" % (
            self.frequency.shape, self.flux.shape)
    
    @property
    def nchan(self): return self.flux.shape[0]
    
    @property
    def npol(self): return self.flux.shape[1]
    
    def __str__(self):
        """Default printer for Skycomponent

        """
        s = "Skycomponent:\n"
        s += "\tFlux: %s\n" % (self.flux)
        s += "\tDirection: %s\n" % (self.direction)
        s += "\tShape: %s\n" % (self.shape)
        s += "\tParams: %s\n" % (self.params)
        return s


class Skymodel:
    """ A skymodel consisting of a list of images and a list of skycomponents
    
    """
    
    def __init__(self):
        self.images = []  # collection of numpy arrays
        self.components = []  # collection of SkyComponents


class Visibility:
    """ Visibility table class

    Visibility with uvw, time, a1, a2, vis, weight Columns in
    an astropy Table along with an attribute to hold the frequencies
    and an attribute to hold the direction.

    Visibility is defined to hold an observation with one set of frequencies and one
    direction.

    The data column has vis:[row,nchan,npol], uvw:[row,3]
    """
    
    def __init__(self,
                 data=None, frequency=None, phasecentre=None, configuration=None,
                 uvw=None, time=None, antenna1=None, antenna2=None, vis=None, weight=None,
                 imaging_weight=None):
        if data is None and vis is not None:
            if imaging_weight is None:
                imaging_weight = weight
            data = Table({'uvw': uvw, 'time': time,
                          'antenna1': antenna1, 'antenna2': antenna2,
                          'vis': vis, 'weight': weight, 'imaging_weight': imaging_weight
                          })
        
        self.data = data  # Astropy.table with columns uvw, time, a1, a2, vis, weight, imaging_weight
        self.frequency = frequency  # numpy.array [nchan]
        self.phasecentre = phasecentre  # Phase centre of observation
        self.configuration = configuration  # Antenna/station configuration
    
    def __sizeof__(self):
        """ Return size in GB
        """
        size = 0
        size += numpy.size(self.frequency)
        for col in self.data.colnames:
            size += self.data[col].size * sys.getsizeof(self.data[col])
        return size / 1024.0 / 1024.0 / 1024.0
    
    @property
    def nvis(self):
        return self.data['vis'].shape[0]
    
    @property
    def nchan(self):
        return self.data['vis'].shape[1]
    
    @property
    def npol(self):
        return self.data['vis'].shape[2]
    
    @property
    def uvw(self):
        return self.data['uvw']
    
    @property
    def u(self):
        return self.data['uvw'][:, 0]
    
    @property
    def v(self):
        return self.data['uvw'][:, 1]
    
    @property
    def w(self):
        return self.data['uvw'][:, 2]
    
    @property
    def time(self):
        return self.data['time']
    
    @property
    def antenna1(self):
        return self.data['antenna1']
    
    @property
    def antenna2(self):
        return self.data['antenna2']
    
    @property
    def vis(self):
        return self.data['vis']
    
    @property
    def weight(self):
        return self.data['weight']
    
    @property
    def imaging_weight(self):
        return self.data['imaging_weight']
    
    def uvw_lambda(self, channel=0):
        """ Calculates baseline coordinates in wavelengths. """
        return self.data['uvw'] * self.frequency[channel] / c.value


class QA:
    """ Quality assessment
    
    """
    
    def __init__(self, origin=None, data=None, context=None):
        self.origin = origin  # Name of function originating QA assessment
        self.data = data  # Dictionary containing standard fields
        self.context = context  # Context string (TBD)
    
    def __str__(self):
        """Default printer for QA
        
        """
        s = "Quality assessment:\n"
        s += "\tOrigin: %s\n" % (self.origin)
        s += "\tContext: %s\n" % (self.context)
        s += "\tData:\n"
        for dataname in self.data.keys():
            s += "\t\t%s: %s\n" % (dataname, str(self.data[dataname]))
        return s


def assert_same_chan_pol(o1, o2):
    """
    Assert that two entities indexed over channels and polarisations
    have the same number of them.
    """
    assert o1.npol == o2.npol, \
        "%s and %s have different number of polarisations: %d != %d" % \
        (type(o1).__name__, type(o2).__name__, o1.npol, o2.npol)
    assert o1.nchan == o2.nchan, \
        "%s and %s have different number of channels: %d != %d" % \
        (type(o1).__name__, type(o2).__name__, o1.nchan, o2.nchan)