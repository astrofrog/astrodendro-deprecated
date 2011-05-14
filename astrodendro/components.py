import string
import numpy as np


class Leaf(object):

    def __init__(self, x, y, z, f, id=None):
        self.x = np.array([x], dtype=int)
        self.y = np.array([y], dtype=int)
        self.z = np.array([z], dtype=int)
        self.f = np.array([f], dtype=float)
        self.xmin, self.xmax = x, x
        self.ymin, self.ymax = y, y
        self.zmin, self.zmax = z, z
        self.fmin, self.fmax = f, f
        self.id = id
        self.parent = None

    def __getattr__(self, attribute):
        if attribute == 'npix':
            return len(self.x)
        else:
            raise Exception("Attribute not found: %s" % attribute)

    def add_point(self, x, y, z, f):
        "Add point to current leaf"
        self.x = np.hstack([self.x, x])
        self.y = np.hstack([self.y, y])
        self.z = np.hstack([self.z, z])
        self.f = np.hstack([self.f, f])
        self.xmin, self.xmax = min(x, self.xmin), max(x, self.xmax)
        self.ymin, self.ymax = min(y, self.ymin), max(y, self.ymax)
        self.zmin, self.zmax = min(z, self.zmin), max(z, self.zmax)
        self.fmin, self.fmax = min(f, self.fmin), max(f, self.fmax)

    def merge(self, leaf):
        self.x = np.hstack([self.x, leaf.x])
        self.y = np.hstack([self.y, leaf.y])
        self.z = np.hstack([self.z, leaf.z])
        self.f = np.hstack([self.f, leaf.f])
        self.xmin, self.xmax = min(np.min(leaf.x), self.xmin), max(np.max(leaf.x), self.xmax)
        self.ymin, self.ymax = min(np.min(leaf.y), self.ymin), max(np.max(leaf.y), self.ymax)
        self.zmin, self.zmax = min(np.min(leaf.z), self.zmin), max(np.max(leaf.z), self.zmax)
        self.fmin, self.fmax = min(np.min(leaf.f), self.fmin), max(np.max(leaf.f), self.fmax)

    def add_footprint(self, image, level):
        "Fill in a map which shows the depth of the tree"
        image[self.z, self.y, self.x] = level
        return image

    def plot_dendrogram(self, ax, base_level, lines):
        line = [(self.id, np.max(self.f)), (self.id, base_level)]
        lines.append(line)
        return lines

    def set_id(self, leaf_id):
        self.id = leaf_id
        return leaf_id + 1

    def to_newick(self):
        return "%i:%.3f" % (self.id, self.fmax - self.fmin)


class Branch(Leaf):

    def __init__(self, items, x, y, z, f, id=None):
        self.items = items
        for item in items:
            item.parent = self
        Leaf.__init__(self, x, y, z, f, id=id)

    def __getattr__(self, attribute):
        if attribute == 'npix':
            npix = len(self.x)
            for item in self.items:
                npix += item.npix
            return npix
        else:
            raise AttributeError("Attribute not found: %s" % attribute)

    def add_footprint(self, image, level, recursive=True):
        if recursive:
            for item in self.items:
                image = item.add_footprint(image, level + 1)
        return Leaf.add_footprint(self, image, level)

    def plot_dendrogram(self, ax, base_level, lines):
        line = [(self.id, np.min(self.f)), (self.id, base_level)]
        lines.append(line)
        items_ids = [item.id for item in self.items]
        line = [(np.min(items_ids), np.min(self.f)), \
                (np.max(items_ids), np.min(self.f))]
        lines.append(line)
        for item in self.items:
            lines = item.plot_dendrogram(ax, np.min(self.f), lines)
        return lines

    def set_id(self, start):
        item_id = start
        for item in self.items:
            if not hasattr(self, 'id'):
                item_id = item.set_id(item_id)
        self.id = np.mean([item.id for item in self.items])
        return item_id

    def to_newick(self):
        newick_items = []
        for item in self.items:
            newick_items.append(item.to_newick())
        return "(%s)%s:%.3f" % (string.join(newick_items, ','), self.id, self.fmax - self.fmin)


class Trunk(list):
    def to_newick(self):
        newick_items = []
        for item in self:
            newick_items.append(item.to_newick())
        return "(%s);" % string.join(newick_items, ',')
