#!/usr/bin/env python
"""Simple wrapper for qsub which provides the functionality of the -sync option
Usage: qsubwt [qsub options] <script.sh>
"""

import sys
import os
import re
import subprocess
import time
import logging

from .version import __version__

QSTAT_INTERVAL = 2
QSUB_JOB_ID_DECODER = "(\d+) \("

DEBUG = False

log = logging.getLogger(__name__)


def _setupLog(file_name=None):
    if file_name is None:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(file_name)

    str_formatter = '[%(levelname)s %(asctime)s] %(message)s'
    formatter = logging.Formatter(str_formatter)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)


class QSubError(Exception):
    pass


class QSubWrapper(object):

    def __init__(self):
        self.scriptToRun = None
        self.jobIdDecoder = None
        self.qstatCmd = None
        self.qsubArgs = None
        self.debug = False
        self.__parseArgs()

    def __parseArgs(self):
        """Handle command line argument parsing"""
        args = sys.argv[1:]

        log.debug("Parsing args %s" % args)

        if len(args) == 0 or "-h" in args or "--help" in args:
            sys.exit(__doc__ + "version: %s" % __version__)

        self.scriptToRun = args.pop()

        if '-sync' in args:
            idx = args.index('-sync')
            args.pop(idx)
            args.pop(idx)

        self.qstatCmd = "qstat"
        self.jobIdDecoder = QSUB_JOB_ID_DECODER

        self.qsubArgs = " ".join(args)

    def _waitForJobTermination(self, jobId):
        """
        Loop until we no longer see the job in qstat
        """
        log.info("waiting for jobId %s to complete" % jobId)

        consecutiveFailures = 0

        while True:
            cmd = "%s -j %s" % (self.qstatCmd, jobId)

            log.debug("calling cmd %s" % cmd)
            with open(os.devnull, "w") as null:
                retCode = subprocess.call(cmd, shell=True,
                                          stderr=null,
                                          stdout=null)
            if retCode > 0:
                break
            time.sleep(QSTAT_INTERVAL)
        log.info(
            "Completed waiting for termination of jobId %s" % jobId)

    def run(self):
        """
        Submits the command using qsub. Monitors progress using qstat.
        Returns with the exit code of the job
        """

        try:
            cmd = "qsub %s" % self.qsubArgs
            cmd = cmd.strip() + " " + self.scriptToRun
            log.info("calling cmd : %s" % cmd)
            output = subprocess.check_output(cmd, shell=True)

            match = re.search(self.jobIdDecoder.encode(), output)

            if match:
                jobId = match.group(1).decode()
            else:
                msg = "Unable to derive jobId from qsub output %s using pattern %s" % (
                    output, self.jobIdDecoder)
                raise QSubError(msg)

            self._waitForJobTermination(jobId)
            return

        except KeyboardInterrupt:
            cmd = "qdel %s" % jobId
            retCode = subprocess.call(cmd, shell=True)

            if retCode != self.successCode:
                msg = "Unable to qdel running job %s. You may have to kill it manually" % jobId
                raise QSubError(msg)


def main():
    if DEBUG:
        _setupLog()
        log.info("Running %s version %s" %
                 (os.path.dirname(__file__), __version__))
    app = QSubWrapper()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
