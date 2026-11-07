"""Protocol checks without a physical toilet or Home Assistant installation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import threading
import time
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "custom_components.xjx_toilet_pro"


class FakeDevice:
    """Record commands that would have been sent through python-miio."""

    def __init__(self, ip: str, token: str, model: str) -> None:
        self.commands: list[tuple[str, object]] = []
        self.properties: dict[str, object] = {"seating": 1, "left_day": 1180}

    def send(self, command: str, parameters: object = None) -> str:
        self.commands.append((command, parameters))
        return "ok"

    def get_properties(self, names: list[str], max_properties: int) -> list[object]:
        return [self.properties[name] for name in names]


def load_api() -> types.ModuleType:
    """Load the API module with a fake miIO dependency."""
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(ROOT / "custom_components" / "xjx_toilet_pro")]
    const = types.ModuleType(f"{PACKAGE}.const")
    const.MODEL_XJX_TOILET_PRO = "xjx.toilet.pro"
    miio = types.ModuleType("miio")
    miio.Device = FakeDevice
    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE}.api", ROOT / "custom_components" / "xjx_toilet_pro" / "api.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        sys.modules,
        {PACKAGE: package, f"{PACKAGE}.const": const, "miio": miio, spec.name: module},
    ):
        spec.loader.exec_module(module)
    return module


api = load_api()


class ProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = api.XjxToiletProClient("127.0.0.1", "test-token")

    def test_poll_only_reliable_properties(self) -> None:
        self.assertEqual(api.AVAILABLE_PROPERTIES, ["seating", "left_day"])
        self.assertEqual(self.client.status(), api.ToiletLidStatus(True, 180))

    def test_commands_use_levels_instead_of_degrees(self) -> None:
        with patch.object(api, "MIN_COMMAND_GAP_SECONDS", 0):
            self.client.set_seat_temperature(2)
            self.client.set_fan_temperature(3)
            self.client.set_rear_wash_water_temperature(1)
            self.client.set_warm_air_drying(True)
            self.client.set_rear_wash(True)
        self.assertEqual(
            self.client.commands,
            [
                ("set_seat_temp", [2]),
                ("warm_dry_on", [3]),
                ("tun_wash_on", [1, 2, 2, 1, 0]),
                ("warm_dry_on", [3]),
                ("tun_wash_on", [1, 2, 2, 1, 0]),
            ],
        )
        with self.assertRaises(ValueError):
            self.client.set_seat_temperature(35)
        with self.assertRaises(ValueError):
            self.client.set_fan_temperature(43)

    def test_concurrent_packets_are_serialized_and_spaced(self) -> None:
        timestamps: list[float] = []
        started = threading.Barrier(3)
        original_send = FakeDevice.send

        def record_send(device: FakeDevice, command: str, parameters: object = None) -> str:
            timestamps.append(time.monotonic())
            return original_send(device, command, parameters)

        def worker() -> None:
            started.wait()
            self.client.raw_command("get_prop", ["seating"])

        threads = [threading.Thread(target=worker) for _ in range(2)]
        with patch.object(FakeDevice, "send", record_send):
            for thread in threads:
                thread.start()
            started.wait()
            for thread in threads:
                thread.join(timeout=3)
        self.assertEqual(len(timestamps), 2)
        self.assertGreaterEqual(
            timestamps[1] - timestamps[0], api.MIN_COMMAND_GAP_SECONDS - 0.01
        )


if __name__ == "__main__":
    unittest.main()
