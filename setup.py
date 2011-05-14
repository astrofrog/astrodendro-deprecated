#!/usr/bin/env python

from distutils.core import setup

try:  # Python 3.x
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:  # Python 2.x
    from distutils.command.build_py import build_py

setup(name='Astronomical Dendrograms',
      version='0.1.0',
      description='Astronomical Dendrograms',
      author='Thomas Robitaille',
      author_email='thomas.robitaille@gmail.com',
      packages=['astrodendro'],
      provides=['astrodendro'],
      requires=['numpy'],
      cmdclass={'build_py': build_py},
      keywords=['Scientific/Engineering'],
      classifiers=[
                   "Development Status :: 3 - Alpha",
                   "Programming Language :: Python",
                   "License :: OSI Approved :: MIT License",
                  ],
     )
