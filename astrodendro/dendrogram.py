# Computing Astronomical Dendrograms
# Copyright (c) 2011 Thomas P. Robitaille
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# Notes:
# - An item is a leaf or a branch
# - An ancestor is the largest structure that an item is part of

import numpy as np

from astrodendro.components import Trunk, Branch, Leaf
from astrodendro.meshgrid import meshgrid_nd
from astrodendro.newick import parse_newick


class Dendrogram(object):

    def __init__(self, *args, **kwargs):

        if len(args) == 1:
            self._compute(*args, **kwargs)

        self._reset_idx()

    def _reset_idx(self):
        self._idx_counter = 0

    def _next_idx(self):
        self._idx_counter += 1
        return self._idx_counter

    def _compute(self, data, minimum_flux=-np.inf, minimum_npix=0, minimum_delta=0, verbose=True):

        # Reset ID counter
        self._reset_idx()

        # Initialize list of ancestors
        ancestor = {}

        # If array is 2D, recast to 3D
        if len(data.shape) == 2:
            self.n_dim = 2
            self.data = data.reshape(1, data.shape[0], data.shape[1])
        else:
            self.n_dim = 3
            self.data = data

        # Extract data shape
        nz, ny, nx = self.data.shape

        # Create arrays with pixel positions
        x = np.arange(self.data.shape[2], dtype=np.int32)
        y = np.arange(self.data.shape[1], dtype=np.int32)
        z = np.arange(self.data.shape[0], dtype=np.int32)
        X, Y, Z = meshgrid_nd(x, y, z)

        # Convert to 1D
        flux, X, Y, Z = self.data.ravel(), X.ravel(), Y.ravel(), Z.ravel()

        # Keep only values above minimum required
        keep = flux > minimum_flux
        flux, X, Y, Z = flux[keep], X[keep], Y[keep], Z[keep]
        if verbose:
            print "Number of points above minimum: %i" % np.sum(keep)

        # Sort by decreasing flux
        order = np.argsort(flux)[::-1]
        flux, X, Y, Z = flux[order], X[order], Y[order], Z[order]

        # Define index array indicating what item each cell is part of
        self.index_map = np.zeros(self.data.shape, dtype=np.int32)

        # Loop from largest to smallest value. Each time, check if the pixel
        # connects to any existing leaf. Otherwise, create new leaf.

        items = {}

        for i in range(len(flux)):

            # Print stats
            if verbose and i % 10000 == 0:
                print "%i..." % i

            # Check if point is adjacent to any leaf
            adjacent = []
            if X[i] > 0 and self.index_map[Z[i], Y[i], X[i] - 1] > 0:
                adjacent.append(self.index_map[Z[i], Y[i], X[i] - 1])
            if X[i] < nx - 1 and self.index_map[Z[i], Y[i], X[i] + 1] > 0:
                adjacent.append(self.index_map[Z[i], Y[i], X[i] + 1])
            if Y[i] > 0 and self.index_map[Z[i], Y[i] - 1, X[i]] > 0:
                adjacent.append(self.index_map[Z[i], Y[i] - 1, X[i]])
            if Y[i] < ny - 1 and self.index_map[Z[i], Y[i] + 1, X[i]] > 0:
                adjacent.append(self.index_map[Z[i], Y[i] + 1, X[i]])
            if Z[i] > 0 and self.index_map[Z[i] - 1, Y[i], X[i]] > 0:
                adjacent.append(self.index_map[Z[i] - 1, Y[i], X[i]])
            if Z[i] < nz - 1 and self.index_map[Z[i] + 1, Y[i], X[i]] > 0:
                adjacent.append(self.index_map[Z[i] + 1, Y[i], X[i]])

            # Replace adjacent elements by its ancestor
            for j in range(len(adjacent)):
                if ancestor[adjacent[j]] is not None:
                    adjacent[j] = ancestor[adjacent[j]]

            # Remove duplicates
            adjacent = list(set(adjacent))

            # Find how many unique adjacent structures there are
            n_adjacent = len(adjacent)

            if n_adjacent == 0:  # Create new leaf

                # Set absolute index of the new element
                idx = self._next_idx()

                # Create leaf
                leaf = Leaf(X[i], Y[i], Z[i], flux[i], id=idx)

                # Add leaf to overall list
                items[idx] = leaf

                # Set absolute index of pixel in index map
                self.index_map[Z[i], Y[i], X[i]] = idx

                # Create new entry for ancestor
                ancestor[idx] = None

            elif n_adjacent == 1:  # Add to existing leaf or branch

                # Get absolute index of adjacent element
                idx = adjacent[0]

                # Get adjacent item
                item = items[idx]

                # Add point to item
                item.add_point(X[i], Y[i], Z[i], flux[i])

                # Set absolute index of pixel in index map
                self.index_map[Z[i], Y[i], X[i]] = idx

            else:  # Merge leaves

                # At this stage, the adjacent items might consist of an arbitrary
                # number of leaves and branches.

                # Find all leaves that are not important enough to be kept
                # separate. These leaves will now be treated the same as the pixel
                # under consideration
                merge = []
                for idx in adjacent:
                    if type(items[idx]) == Leaf:
                        leaf = items[idx]
                        if leaf.npix < minimum_npix or leaf.fmax - flux[i] < minimum_delta:
                            merge.append(idx)

                # Remove merges from list of adjacent items
                for idx in merge:
                    adjacent.remove(idx)

                # If there is only one item left, then if it is a leaf, add to the
                # list to merge, and if it is a branch then add the merges to the
                # branch.

                if len(adjacent) == 0:

                    # There are no separate leaves left (and no branches), so pick the
                    # first one as the reference and merge all the others onto it

                    idx = merge[0]
                    leaf = items[idx]

                    # Add current point to the leaf
                    leaf.add_point(X[i], Y[i], Z[i], flux[i])

                    # Set absolute index of pixel in index map
                    self.index_map[Z[i], Y[i], X[i]] = idx

                    for i in merge[1:]:

                        # print "Merging leaf %i onto leaf %i" % (i, idx)

                        # Remove leaf
                        removed = items.pop(i)

                        # Merge old leaf onto reference leaf
                        leaf.merge(removed)

                        # Update index map
                        self.index_map = removed.add_footprint(self.index_map, idx)

                elif len(adjacent) == 1:

                    if type(items[adjacent[0]]) == Leaf:

                        idx = adjacent[0]
                        leaf = items[idx]

                        # Add current point to the leaf
                        leaf.add_point(X[i], Y[i], Z[i], flux[i])

                        # Set absolute index of pixel in index map
                        self.index_map[Z[i], Y[i], X[i]] = idx

                        for i in merge:

                            # print "Merging leaf %i onto leaf %i" % (i, idx)

                            # Remove leaf
                            removed = items.pop(i)

                            # Merge old leaf onto reference leaf
                            leaf.merge(removed)

                            # Update index map
                            self.index_map = removed.add_footprint(self.index_map, idx)

                    else:

                        idx = adjacent[0]
                        branch = items[idx]

                        # Add current point to the branch
                        branch.add_point(X[i], Y[i], Z[i], flux[i])

                        # Set absolute index of pixel in index map
                        self.index_map[Z[i], Y[i], X[i]] = idx

                        for i in merge:

                            # print "Merging leaf %i onto branch %i" % (i, idx)

                            # Remove leaf
                            removed = items.pop(i)

                            # Merge old leaf onto reference leaf
                            branch.merge(removed)

                            # Update index map
                            self.index_map = removed.add_footprint(self.index_map, idx)

                else:

                    # Set absolute index of the new element
                    idx = self._next_idx()

                    # Create branch
                    branch = Branch([items[j] for j in adjacent], \
                                    X[i], Y[i], Z[i], flux[i], id=idx)

                    # Add branch to overall list
                    items[idx] = branch

                    # Set absolute index of pixel in index map
                    self.index_map[Z[i], Y[i], X[i]] = idx

                    # Create new entry for ancestor
                    ancestor[idx] = None

                    for i in merge:

                        # print "Merging leaf %i onto branch %i" % (i, idx)

                        # Remove leaf
                        removed = items.pop(i)

                        # Merge old leaf onto reference leaf
                        branch.merge(removed)

                        # Update index map
                        self.index_map = removed.add_footprint(self.index_map, idx)

                    for j in adjacent:
                        ancestor[j] = idx
                        for a in ancestor:
                            if ancestor[a] == j:
                                ancestor[a] = idx

        if verbose and not i % 10000 == 0:
            print "%i..." % i

        # Remove orphan leaves that aren't large enough
        remove = []
        for idx in items:
            item = items[idx]
            if type(item) == Leaf:
                if item.npix < minimum_npix or item.fmax - item.fmin < minimum_delta:
                    remove.append(idx)
        for idx in remove:
            items.pop(idx)

        # Create trunk from objects with no ancestors
        self.trunk = Trunk()
        for idx in items:
            if ancestor[idx] is None:
                self.trunk.append(items[idx])

        # Make map of leaves vs branches
        self.item_type_map = np.zeros(self.data.shape, dtype=np.uint8)
        for idx in items:
            item = items[idx]
            if type(item) == Leaf:
                self.item_type_map = item.add_footprint(self.item_type_map, 2)
            else:
                self.item_type_map = item.add_footprint(self.item_type_map, 1, recursive=False)

        # Re-cast to 2D if original dataset was 2D
        if self.n_dim == 2:
            self.data = self.data[0, :, :]
            self.index_map = self.index_map[0, :, :]
            self.item_type_map = self.item_type_map[0, :, :]

    def get_leaves(self):
        return self.trunk.get_leaves()

    def to_newick(self):
        return self.trunk.to_newick()

    def to_hdf5(self, filename):

        import h5py

        f = h5py.File(filename, 'w')

        f.attrs['n_dim'] = self.n_dim

        f.create_dataset('newick', data=self.to_newick())

        d = f.create_dataset('index_map', data=self.index_map, compression=True)
        d.attrs['CLASS'] = 'IMAGE'
        d.attrs['IMAGE_VERSION'] = '1.2'
        d.attrs['IMAGE_MINMAXRANGE'] = [self.index_map.min(), self.index_map.max()]

        d = f.create_dataset('item_type_map', data=self.item_type_map, compression=True)
        d.attrs['CLASS'] = 'IMAGE'
        d.attrs['IMAGE_VERSION'] = '1.2'
        d.attrs['IMAGE_MINMAXRANGE'] = [self.item_type_map.min(), self.item_type_map.max()]

        d = f.create_dataset('data', data=self.data, compression=True)
        d.attrs['CLASS'] = 'IMAGE'
        d.attrs['IMAGE_VERSION'] = '1.2'
        d.attrs['IMAGE_MINMAXRANGE'] = [self.data.min(), self.data.max()]

        f.close()

    def from_hdf5(self, filename):

        import h5py

        f = h5py.File(filename, 'r')

        self.n_dim = f.attrs['n_dim']

        # If array is 2D, reshape to 3D
        if self.n_dim == 2:
            self.data = f['data'].value.reshape(1, f['data'].shape[0], f['data'].shape[1])
            self.index_map = f['index_map'].value.reshape(1, f['data'].shape[0], f['data'].shape[1])
            self.item_type_map = f['item_type_map'].value.reshape(1, f['data'].shape[0], f['data'].shape[1])
        else:
            self.data = f['data'].value
            self.index_map = f['index_map'].value
            self.item_type_map = f['item_type_map'].value

        # Extract data shape
        nz, ny, nx = self.data.shape

        # Create arrays with pixel positions
        x = np.arange(self.data.shape[2], dtype=np.int32)
        y = np.arange(self.data.shape[1], dtype=np.int32)
        z = np.arange(self.data.shape[0], dtype=np.int32)
        X, Y, Z = meshgrid_nd(x, y, z)

        tree = parse_newick(f['newick'].value)

        def construct_tree(d):
            items = []
            for idx in d:
                x = X[self.index_map == idx]
                y = Y[self.index_map == idx]
                z = Z[self.index_map == idx]
                f = self.data[self.index_map == idx]
                if type(d[idx]) == tuple:
                    sub_items = construct_tree(d[idx][0])
                    b = Branch(sub_items, x[0], y[0], z[0], f[0], id=idx)
                    for i in range(1, len(x)):
                        b.add_point(x[i], y[i], z[i], f[i])
                    items.append(b)
                else:
                    l = Leaf(x[0], y[0], z[0], f[0], id=idx)
                    for i in range(1, len(x)):
                        l.add_point(x[i], y[i], z[i], f[i])
                    items.append(l)
            return items

        self.trunk = Trunk()
        for item in construct_tree(tree):
            self.trunk.append(item)

        # Re-cast to 2D if original dataset was 2D
        if self.n_dim == 2:
            self.data = self.data[0, :, :]
            self.index_map = self.index_map[0, :, :]
            self.item_type_map = self.item_type_map[0, :, :]
