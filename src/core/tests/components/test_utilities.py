from optibar_core.src.components.utilities import round_up, round_down

def test_round_up():
    assert round_up(1.23, 0.05) == 1.25
    assert round_up(.3, 0.05) == 0.3
    assert round_up(.03, 0.05) == 0.05
    assert round_up(1.2, 0.1) == 1.2
    assert round_up(.08, 0.1) == .10
    assert round_up(.78, 0.2) == .8

def test_round_down():
    assert round_down(1.23, 0.05) == 1.20
    assert round_down(.3, 0.05) == 0.3
    assert round_down(.03, 0.05) == 0.00
    assert round_down(1.2, 0.1) == 1.2
    assert round_down(.08, 0.1) == 0
    assert round_down(.78, 0.2) == .6