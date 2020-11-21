"""
    created on oct 2020

    :file: timer.py
    :platform: Linux, Windows
    :synopsis:
        contains timer class.
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""

import time


class Timer:
    """
    Timer class
    """
    def __init__(self, timeout):
        """
        :param timeout: timeout in seconds
        """
        self.set_timeout(timeout)
        self.start_time = None

    def set_timeout(self, timeout):
        """
        set timeout
        :param timeout: timeout in seconds
        """
        self.timeout = timeout

    def start(self, timeout=None):
        """
        start timer
        :param timeout: timeout in seconds
        """
        if timeout is not None:
            self.set_timeout(timeout)
        self.start_time = time.time()

    def stop(self):
        """
        stop timer
        """
        self.start_time = None

    def elapsed(self):
        """
        Check the elapsed time
        :return: remaining time
        """
        if self.start_time is not None:
            return time.time() - self.start_time
        return 0

    def is_timed_out(self):
        """
        :return: True if timed out
        """
        if self.is_stopped():
            return False
        return self.elapsed() > self.timeout or self.timeout == 0

    def is_stopped(self):
        """
        check if timeout is stopped
        :return: True if stopped
        """
        return self.start_time is None
