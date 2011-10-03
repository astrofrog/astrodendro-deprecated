import pyfits
from astrodendro import Dendrogram

# Read in the data
image = pyfits.getdata('data.fits.gz')

# Compute the dendrogram
d = Dendrogram(image)

# Output to HDF5 file
d.to_hdf5('simple_2d_dendrogram.hdf5')