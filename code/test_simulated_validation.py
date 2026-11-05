"""Validation test structure with simulated instruments.

These tests run without any hardware. The instruments are replaced by a
simulated class that returns configurable readings, so the file shows how a
validation sequence is organized (interlock check, contact resistance,
insulation resistance) and that each check fails when the reading is bad.
Nothing here is a measurement.

Run with:  pytest examples -v
"""
import time

import pytest


# --- Simulated instrument -------------------------------------------------
class MockInstrument:
    """Answers SCPI-style queries from a table of canned readings."""

    DEFAULTS = {
        "MEAS:RES?": "0.00012",     # 120 micro-ohms, good connection
        "MEAS:ISOL?": "5000000000",  # 5 giga-ohms, good insulation
        "LOCK?": "1",               # shield door locked
    }

    def __init__(self, overrides=None):
        self.responses = {**self.DEFAULTS, **(overrides or {})}
        self.sent = []

    def query(self, cmd):
        for key, value in self.responses.items():
            if key in cmd:
                return value
        return "OK"

    def write(self, cmd):
        self.sent.append(cmd)

    def close(self):
        pass


# --- Checks (each one asserts against a limit) -----------------------------
MAX_CONTACT_RESISTANCE_OHMS = 200e-6     # contact resistance under 200 micro-ohms
MIN_INSULATION_RESISTANCE_OHMS = 1e9     # at least 1 giga-ohm under stress


def check_interlock(fixture):
    """The enclosure shield must be closed before power is applied."""
    is_locked = int(fixture.query("FIXTURE:SAFETY:LOCK?"))
    assert is_locked == 1, "Enclosure door is open. Aborting."


def check_joint_resistance(dmm):
    """Low-ohm measurement across a power terminal connection."""
    resistance = float(dmm.query("MEAS:RES? ROUTE:TERM1"))
    assert resistance < MAX_CONTACT_RESISTANCE_OHMS, (
        f"Loose joint: {resistance * 1e6:.2f} uOhm exceeds "
        f"{MAX_CONTACT_RESISTANCE_OHMS * 1e6:.0f} uOhm."
    )
    return resistance


def check_insulation(hipot, hold_seconds=2.0):
    """Apply a DC voltage, read isolation resistance, then switch the output off."""
    hipot.write("SOUR:VOLT 1000")
    hipot.write("OUTPUT ON")
    try:
        time.sleep(hold_seconds)
        isolation = float(hipot.query("MEAS:ISOL?"))
    finally:
        hipot.write("OUTPUT OFF")          # always discharge, even if the read fails
    assert isolation >= MIN_INSULATION_RESISTANCE_OHMS, (
        f"Insulation dropped to {isolation / 1e6:.2f} MOhm."
    )
    return isolation


# --- Fixture ---------------------------------------------------------------
@pytest.fixture(scope="module")
def instruments():
    """Set up the simulated bench, apply safety limits, and shut down afterward."""
    bench = {"hipot": MockInstrument(), "dmm": MockInstrument(), "fixture": MockInstrument()}
    bench["hipot"].write("SOUR:VOLT:LIMIT 1500")     # cap the voltage at 1500 V
    bench["hipot"].write("SOUR:CURR:LIMIT 0.005")    # trip above 5 mA leakage
    yield bench
    bench["hipot"].write("OUTPUT OFF")
    for device in bench.values():
        device.close()


# --- Tests with good readings ---------------------------------------------
def test_safety_interlock(instruments):
    check_interlock(instruments["fixture"])


def test_connection_integrity(instruments):
    check_joint_resistance(instruments["dmm"])


def test_dielectric_insulation_integrity(instruments):
    check_insulation(instruments["hipot"])


def test_output_is_off_after_insulation_test(instruments):
    assert instruments["hipot"].sent[-1] == "OUTPUT OFF"


# --- Tests with bad readings: each check must fail ---------------------------
def test_open_interlock_is_detected():
    with pytest.raises(AssertionError):
        check_interlock(MockInstrument({"LOCK?": "0"}))


def test_loose_joint_is_detected():
    with pytest.raises(AssertionError):
        check_joint_resistance(MockInstrument({"MEAS:RES?": "0.0005"}))


def test_low_insulation_is_detected():
    hipot = MockInstrument({"MEAS:ISOL?": "500000000"})
    with pytest.raises(AssertionError):
        check_insulation(hipot, hold_seconds=0)
    assert hipot.sent[-1] == "OUTPUT OFF"
