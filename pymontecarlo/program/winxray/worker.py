#!/usr/bin/env python
"""
================================================================================
:mod:`worker` -- WinX-Ray worker
================================================================================

.. module:: worker
   :synopsis: WinX-Ray 2 worker

.. inheritance-diagram:: pymontecarlo.program.winxray.runner.worker

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2012 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import os
import sys
import subprocess
import logging
from zipfile import ZipFile

# Third party modules.

# Local modules.
from pymontecarlo.settings import get_settings
from pymontecarlo.program.worker import SubprocessWorker as _Worker

# Globals and constants variables.
from zipfile import ZIP_DEFLATED

class Worker(_Worker):

    def __init__(self, program):
        """
        Runner to run WinX-Ray simulation(s).
        """
        _Worker.__init__(self, program)

        self._executable = get_settings().winxray.exe
        logging.debug('WinX-Ray executable: %s', self._executable)

        self._executable_dir = os.path.dirname(self._executable)
        logging.debug('WinX-Ray directory: %s', self._executable_dir)

    def run(self, options, outputdir, workdir, *args, **kwargs):
        if sys.platform == 'darwin':
            self.create(options, outputdir, *args, **kwargs)
            raise NotImplementedError("Simulations with WinXRay cannot be directly run. "
                "The .wxc file was created in the output directory.")

        wxcfilepath = self.create(options, workdir)

        # Launch
        args = [self._executable, wxcfilepath.replace('/', '\\')]
        logging.debug('Launching %s', ' '.join(args))

        self._status = 'Running WinX-Ray'

        self._create_process(args, stdout=subprocess.PIPE,
                             cwd=self._executable_dir)
        self._join_process()

        logging.debug('WinX-Ray ended')

        return self._extract_results(options, outputdir, workdir)

    def _extract_results(self, options, outputdir, workdir):
        resultdirs = [name for name in os.listdir(workdir) \
                      if os.path.isdir(os.path.join(workdir, name)) ]
        resultdirs.sort()
        if not resultdirs:
            raise IOError('Cannot find results directories in %s' % workdir)

        # Import results to pyMonteCarlo
        logging.debug('Importing results from WinXRay')
        path = os.path.join(workdir, resultdirs[-1]) # Take last result folder
        results = self.import_(options, path)

        # Create ZIP with all WinXRay results
        zipfilepath = os.path.join(outputdir, options.name + '.zip')
        with ZipFile(zipfilepath, 'w', compression=ZIP_DEFLATED) as zipfile:
            for filename in os.listdir(workdir):
                filepath = os.path.join(workdir, filename)
                zipfile.write(filepath)

        return results
