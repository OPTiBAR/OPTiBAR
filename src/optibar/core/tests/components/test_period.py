import pytest
from optibar.core.components.period import Period

@pytest.fixture
def period():
    return Period(start=1,end=3)

def test_get_length(period):
    assert period.get_length() == 2

def test_subset(period):
    period_subset = Period(1.5,2.5)
    assert period_subset.is_subset_of(period) 

def test_subset_superset(period):
    period_superset = Period(0.5,3.5)
    assert not period_superset.is_subset_of(period) 

def test_subset_intersection(period):
    period_intersection = Period(0.5,2.5)
    assert not period_intersection.is_subset_of(period)

def test_intersection(period):
    period_intersection = Period(2.5,4)
    assert period.has_intersection_with(period_intersection)

def test_intersection_any_order(period):
    assert Period(2.5,4).has_intersection_with(period)
    assert Period(3,4).has_intersection_with(period)
    assert not Period(5,6).has_intersection_with(period)
    assert not period.has_intersection_with(Period(5,6))

def test_equality(period):
    other = Period(1,3)
    assert other == period