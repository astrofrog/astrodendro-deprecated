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

    >>> from astrodendro import Dendrogram
    >>> d = Dendrogram(array)

where ``array`` can be read in from a FITS file for example:

    >>> import pyfits
    >>> array = pyfits.getdata('observations.fits')

(but ``array`` can also be generated in memory, or read in from other
files, e.g. HDF5)

The tree can be explored from the trunk:

    >>> d.trunk
    [<astrodendro.components.Branch object at 0x10279b250>]

This is a list of the lowest structures. We can select one of these:

    >>> d.trunk[0]
    <astrodendro.components.Branch object at 0x10279b250>

Sub-structures of branches can then be retrieved as a list with the ``items`` attribute:

    >>> d.trunk[0].items
    [<astrodendro.components.Branch object at 0x10279b1d0>, <astrodendro.components.Leaf object at 0x10279b210>]

    >>> d.trunk[0].items[0].items
    [<astrodendro.components.Leaf object at 0x10279b150>, <astrodendro.components.Branch object at 0x10279b190>]

The pixel positions and fluxes of all the pixels in a leaf can then be retrieved with the ``x``, ``y``, and ``f`` attributes:

    >>> d.trunk[0].items[0].items[0].x
    array([60, 60])
    >>> d.trunk[0].items[0].items[0].y
    array([16, 15])
    >>> d.trunk[0].items[0].items[0].f
    array([-0.08147667, -0.08692939])

It is also possible to directly retrieve all the leaves:

    >>> leaves = d.get_leaves()

Options
=======

There are several options that can be used when initializing a
``Dendrogram`` object:

* ``minimum_flux`` - the minimum flux of pixels to be used in the
  dendrogram (default is -infinity)
* ``minimum_npix`` - the minimum number of pixels necessary to create a
  new leaf (default is 0)
* ``minimum_delta`` - the minimum flux difference for two structures to
  be treated as being separate (minimum is 0)

For example:

    d = Dendrogram(array, minimum_flux=1.2, minimum_npix=10, minimum_delta=0.1)

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
