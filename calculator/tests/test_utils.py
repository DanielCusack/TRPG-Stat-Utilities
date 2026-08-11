import pytest

from calculator.utils import (
    binomial_probability,
    calculate_promoted_stat,
    cumulative_binomial_probability_at_least,
    cumulative_binomial_probability_at_most,
    expected_stat,
)


class TestExpectedStat:
    def test_below_cap(self):
        assert expected_stat(base=5, growth=50, start_level=1, end_level=5, cap=99) == 7

    def test_clamped_at_cap(self):
        assert (
            expected_stat(base=10, growth=100, start_level=1, end_level=20, cap=15) == 15
        )

    def test_no_level_change_returns_base(self):
        assert expected_stat(base=12, growth=75, start_level=3, end_level=3, cap=99) == 12


class TestCalculatePromotedStat:
    def test_below_cap(self):
        assert calculate_promoted_stat(base=10, bonus=5, cap=20) == 15

    def test_clamped_at_cap(self):
        assert calculate_promoted_stat(base=18, bonus=5, cap=20) == 20


class TestBinomialProbability:
    def test_middle_outcome(self):
        assert binomial_probability(n=2, r=1, p=0.5) == pytest.approx(0.5)

    def test_zero_occurrences(self):
        assert binomial_probability(n=5, r=0, p=0.3) == pytest.approx(0.16807)

    def test_all_occurrences(self):
        assert binomial_probability(n=3, r=3, p=0.4) == pytest.approx(0.064)


class TestCumulativeBinomialProbabilityAtMost:
    def test_full_range_sums_to_one(self):
        assert cumulative_binomial_probability_at_most(
            total=6, occurances=6, event_probability=0.35
        ) == pytest.approx(1)

    def test_zero_occurrences_matches_single_probability(self):
        # 0.6**4, computed independently of binomial_probability
        assert cumulative_binomial_probability_at_most(
            total=4, occurances=0, event_probability=0.4
        ) == pytest.approx(0.1296)

    def test_known_value(self):
        assert cumulative_binomial_probability_at_most(
            total=2, occurances=1, event_probability=0.5
        ) == pytest.approx(0.75)


class TestCumulativeBinomialProbabilityAtLeast:
    def test_zero_occurrences_sums_to_one(self):
        assert cumulative_binomial_probability_at_least(
            total=5, occurances=0, event_probability=0.6
        ) == pytest.approx(1)

    def test_all_occurrences_matches_single_probability(self):
        # 0.4**4, computed independently of binomial_probability
        assert cumulative_binomial_probability_at_least(
            total=4, occurances=4, event_probability=0.4
        ) == pytest.approx(0.0256)

    def test_complements_at_most(self):
        total, occurances, p = 7, 3, 0.45
        at_least = cumulative_binomial_probability_at_least(total, occurances, p)
        at_most = cumulative_binomial_probability_at_most(total, occurances - 1, p)
        assert at_least + at_most == pytest.approx(1)
