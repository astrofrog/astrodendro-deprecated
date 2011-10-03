About
=====

The aim of this Python module is to make it easy to compute dendrograms
of Astronomical data. The use of dendrograms to represent Astronomical
data is described in detail in [Goodman, A. (2009,
Nature)](http://adsabs.harvard.edu/abs/2009Natur.457...63G).

Installing
==========

To install the ``astrodendro`` module, simply do:

    python setup.py install

Using
=====

Dendrograms can be computed from any 2- or 3-D Numpy array:

    from astrodendro import Dendrogram
    d = Dendrogram(array)

where ``array`` can be read in from a FITS file for example:

    import pyfits
    array = pyfits.getdata('observations.fits')

(but ``array`` can also be generated in memory, or read in from other
files, e.g. HDF5)

Options
=======

There are several options that can be used when initializing a
``Dendrogram`` object:

* ``minimum_flux`` - the minimum flux of pixels to be used in the
  dendrogram
* ``minimum_npix`` - the minimum number of pixels necessary to create a
  new leaf
* ``minimum_delta`` - the minimum flux difference for two structures to
  be treated as being separate

Writing
=======

Dendrograms can be written out and read in from a portable HDF5-based
format:

    # Create dendrogram and write it out
    d = Dendrogram(array)
    d.to_hdf5('observations_dendrogram.hdf5')

    # Read dendrogram into new instance
    d2 = Dendrogram()
    d2.from_hdf5('observations_dendrogram.hdf5')
