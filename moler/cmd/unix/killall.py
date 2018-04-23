# -*- coding: utf-8 -*-
"""
Killall command module.
"""

__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnix
from moler.cmd.converterhelper import ConverterHelper
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Killall(GenericUnix):

    def __init__(self, connection, name, prompt=None, new_line_chars=None, is_verbose=None):
        super(Killall, self).__init__(connection, prompt=prompt, new_line_chars=new_line_chars)
        self._converter_helper = ConverterHelper()
        self.is_verbose = is_verbose
        self.name = name

    def build_command_string(self):
        if self.is_verbose:
            cmd = "{} {} {}".format("killall", self.is_verbose, self.name)
        else:
            cmd = "{} {}".format("killall", self.name)
        return cmd

    def on_new_line(self, line, is_full_line):
        if not is_full_line:
            return super(Killall, self).on_new_line(line, is_full_line)
        try:
            self._parse_no_permit(line)
            self._parse_no_process(line)
            self._parse_killall(line)
        except ParsingDone:
            pass
        return super(Killall, self).on_new_line(line, is_full_line)

    def _parse_no_permit(self, line):
        if self._regex_helper.search(r'(Operation not permitted)', line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group(1))))
            raise ParsingDone

    def _parse_no_process(self, line):
        if self._regex_helper.search(r'(no process found)', line):
            self.current_ret["Status"] = "True"
            raise ParsingDone

    _re_killall = re.compile(r"Killed (?P<Name>[^\(]+)\((?P<Pid>\d+)\) with signal")

    def _parse_killall(self, line):
        if self.is_verbose:
            if self._regex_helper.search_compiled(Killall._re_killall, line):
                if "Detail" not in self.current_ret:
                    self.current_ret["Detail"] = dict()
                pid = self._regex_helper.group("Pid")
                self.current_ret["Detail"][pid] = self._regex_helper.group("Name")
        self.current_ret["Status"] = "True"


COMMAND_OUTPUT_verbose = """
Pclinux90:~ #  killall -v iperf
Killed iperf(15054) with signal 15
Pclinux90:~ #
"""

COMMAND_KWARGS_verbose = {"name": "iperf",
                          "is_verbose": "-v"}

COMMAND_RESULT_verbose = {
    "Status": "True",
    "Detail": {"15054": "iperf"}
}

COMMAND_OUTPUT_no_verbose = """
Pclinux90:~ #  killall iperf
Pclinux90:~ #
"""

COMMAND_KWARGS_no_verbose = {"name": "iperf"}

COMMAND_RESULT_no_verbose = {
    "Status": "True"
}

COMMAND_OUTPUT_no_process = """
PClinux110:/home/runner # killall tshark
tshark: no process found
PClinux110:/home/runner #
"""

COMMAND_KWARGS_no_process = {"name": "tshark"}

COMMAND_RESULT_no_process = {
    "Status": "True"
}