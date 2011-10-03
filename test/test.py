import unittest
import os

import pyfits
from astrodendro import Dendrogram

def test_compute():
    array = pyfits.getdata('data.fits.gz')
    d = Dendrogram(array)
    
def test_write():
    array = pyfits.getdata('data.fits.gz')
    d = Dendrogram(array)
    d.to_hdf5('test.hdf5')
    os.remove('test.hdf5')

def test_read():
    array = pyfits.getdata('data.fits.gz')
    d = Dendrogram(array)
    d.to_hdf5('test.hdf5')
    d2 = Dendrogram()
    d2.from_hdf5('test.hdf5')
    os.remove('test.hdf5')

