#!/usr/bin/env python
"""
Simple wrapper for qsub which provides the functionality of the -sync option
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


def _setupLog(file_name=None):
    log = logging.getLogger()
    if file_name is None:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(file_name)
    str_formatter = '[%(levelname)s %(asctime)s] %(message)s'
    formatter = logging.Formatter(str_formatter)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    return log


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
        self.log.debug("Parsing args %s" % args)
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
        self.log.info("waiting for jobId %s to complete" % jobId)
        consecutiveFailures = 0
        while True:
            cmd = "%s -j %s" % (self.qstatCmd, jobId)
            self.log.debug("calling cmd %s" % cmd)
            with open(os.devnull, "w") as null:
                retCode = subprocess.call(cmd, shell=True,
                                          stderr=null,
                                          stdout=null)
            if retCode > 0:
                break
            time.sleep(QSTAT_INTERVAL)
        self.log.info(
            "Completed waiting for termination of jobId %s" % jobId)

    def run(self):
        """
        Submits the command using qsub. Monitors progress using qstat.
        Returns with the exit code of the job
        """
        try:
            cmd = "qsub %s" % self.qsubArgs
            cmd = cmd.strip() + " " + self.scriptToRun
            self.log.info("calling cmd : %s" % cmd)
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
            if retCode != 0:
                msg = "Unable to qdel running job %s. You may have to kill it manually" % jobId
                raise QSubError(msg)

    @property
    def log(self):
        return logging.getLogger()


def main():
    if len(sys.argv) == 1 or "-h" in sys.argv or "--help" in sys.argv:
        sys.exit(__doc__.strip() + "\nversion: %s" % __version__)
    log = _setupLog()
    if DEBUG:
        log.setLevel(logging.DEBUG)
    log.info("Running qsubwt version %s" % __version__)
    app = QSubWrapper()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
