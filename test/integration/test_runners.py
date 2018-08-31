# -*- coding: utf-8 -*-
"""
Testing connection observer runner API that should be fullfilled by any runner

- submit
- wait_for
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import threading
import time
import platform
import importlib

import pytest
from moler.connection_observer import ConnectionObserver


def test_gets_all_data_of_connection_after_it_is_started(observer_runner):
    from moler.connection import ObservableConnection

    for n in range(20):  # need to test multiple times because of thread races
        moler_conn = ObservableConnection()
        net_down_detector = NetworkDownDetector(connection=moler_conn, runner=observer_runner)
        connection = net_down_detector.connection
        net_down_detector.start()

        connection.data_received("61 bytes")
        connection.data_received("62 bytes")
        connection.data_received("ping: Network is unreachable")

        assert net_down_detector.all_data_received == ["61 bytes", "62 bytes", "ping: Network is unreachable"]


# TODO: tests for error cases


# --------------------------- resources ---------------------------

def is_python35_or_above():
    (ver_major, ver_minor, _) = platform.python_version().split('.')
    return (ver_major == '3') and (int(ver_minor) >= 5)


available_bg_runners = ['runner.ThreadPoolExecutorRunner']
if is_python35_or_above():
    available_bg_runners.append('asyncio_runner.AsyncioRunner')


@pytest.yield_fixture(params=available_bg_runners)
def observer_runner(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    runner_class = getattr(module, class_name)
    runner = runner_class()
    # NOTE: AsyncioRunner given here will start without running event loop
    yield runner
    runner.shutdown()


class NetworkDownDetector(ConnectionObserver):
    def __init__(self, connection=None, runner=None):
        super(NetworkDownDetector, self).__init__(connection=connection, runner=runner)
        self.all_data_received = []

    def data_received(self, data):
        """
        Awaiting change like:
        64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms
        ping: sendmsg: Network is unreachable
        """
        self.all_data_received.append(data)
        if not self.done():
            if "Network is unreachable" in data:
                when_detected = time.time()
                self.set_result(result=when_detected)


@pytest.fixture()
def connection_observer():
    from moler.connection import ObservableConnection
    moler_conn = ObservableConnection()
    observer = NetworkDownDetector(connection=moler_conn)
    return observer


@pytest.fixture()
def observer_and_awaited_data(connection_observer):
    awaited_data = 'ping: sendmsg: Network is unreachable'
    return connection_observer, awaited_data
