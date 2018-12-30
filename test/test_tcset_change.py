# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import

import pytest
import simplejson as json
from subprocrunner import SubprocessRunner
from tcconfig._const import Tc

from .common import execute_tcdel, print_test_result


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


class Test_tcset_change(object):
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:

        python setup.py test --addopts "--device=<test device>"

    These tests expected to execute in the following environment:
       - Linux w/ iputils-ping package
       - English locale (for parsing ping output)
    """

    def test_smoke_multiple(self, device_value):
        if device_value is None:
            pytest.skip("device is null")

        for device_option in [device_value, "--device {}".format(device_value)]:
            execute_tcdel(device_option)

            assert (
                SubprocessRunner(
                    " ".join(
                        [
                            Tc.Command.TCSET,
                            device_option,
                            "--delay 100ms --rate 50k --network 192.168.1.2 --change",
                        ]
                    )
                ).run()
                == 0
            )

            assert (
                SubprocessRunner(
                    " ".join(
                        [
                            Tc.Command.TCSET,
                            device_option,
                            "--delay 100ms --rate 50k --network 192.168.1.3 --change",
                        ]
                    )
                ).run()
                == 0
            )

            execute_tcdel(device_option)

    def test_normal(self, device_value):
        if device_value is None:
            pytest.skip("device is null")

        for device_option in [device_value, "--device {}".format(device_value)]:
            assert (
                SubprocessRunner(
                    " ".join(
                        [
                            Tc.Command.TCSET,
                            device_option,
                            "--delay 100ms --rate 50k --network 192.168.1.2 --overwrite",
                        ]
                    )
                ).run()
                == 0
            )

            assert (
                SubprocessRunner(
                    " ".join(
                        [
                            Tc.Command.TCSET,
                            device_option,
                            "--delay 200.0ms",
                            "--delay-distro 20",
                            "--rate 100k",
                            "--loss 0.01%",
                            "--duplicate 5%",
                            "--reorder 2%",
                            "--network 192.168.1.3",
                            "--add",
                        ]
                    )
                ).run()
                == 0
            )

            runner = SubprocessRunner("{:s} {:s}".format(Tc.Command.TCSHOW, device_option))
            runner.run()

            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
                        "outgoing": {
                            "dst-network=192.168.1.2/32, protocol=ip": {
                                "filter_id": "800::800",
                                "delay": "100.0ms",
                                "rate": "50Kbps"
                            },
                            "dst-network=192.168.1.3/32, protocol=ip": {
                                "filter_id": "800::801",
                                "delay": "200.0ms",
                                "loss": "0.01%",
                                "duplicate": "5%",
                                "delay-distro": "20.0ms",
                                "rate": "100Kbps",
                                "reorder": "2%"
                            }
                        },
                        "incoming": {}
                    }
                }"""
            )

            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)
            assert json.loads(runner.stdout) == json.loads(expected)

            assert (
                SubprocessRunner(
                    " ".join(
                        [
                            Tc.Command.TCSET,
                            device_option,
                            "--delay 300ms",
                            "--delay-distro 30",
                            "--rate 200k",
                            "--loss 0.02%",
                            "--duplicate 5.5%",
                            "--reorder 0.2%",
                            "--network 192.168.1.3",
                            "--change",
                        ]
                    )
                ).run()
                == 0
            )

            runner = SubprocessRunner("{:s} {:s}".format(Tc.Command.TCSHOW, device_option))
            runner.run()

            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
                        "outgoing": {
                            "dst-network=192.168.1.2/32, protocol=ip": {
                                "filter_id": "800::800",
                                "delay": "100.0ms",
                                "rate": "50Kbps"
                            },
                            "dst-network=192.168.1.3/32, protocol=ip": {
                                "filter_id": "800::801",
                                "delay": "300.0ms",
                                "loss": "0.02%",
                                "duplicate": "5.5%",
                                "delay-distro": "30.0ms",
                                "rate": "200Kbps",
                                "reorder": "0.2%"
                            }
                        },
                        "incoming": {}
                    }
                }"""
            )

            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)
            assert json.loads(runner.stdout) == json.loads(expected)

            # finalize ---
            execute_tcdel(device_option)
