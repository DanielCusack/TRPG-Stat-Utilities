import math


def expected_stat(base, growth, start_level: int, end_level: int, cap) -> int:
    return min(base + (end_level - start_level) * (growth / 100), cap)


def calculate_promoted_stat(base, bonus, cap):
    return min(base + bonus, cap)


def binomial_probability(n: int, r: int, p: float):
    return math.comb(n, r) * (p**r) * ((1 - p) ** (n - r))


def cumulative_binomial_probability_at_most(
    total: int, occurances: int, event_probability: float
) -> float:
    return sum(
        binomial_probability(total, i, event_probability) for i in range(occurances + 1)
    )


def cumulative_binomial_probability_at_least(
    total: int, occurances: int, event_probability: float
) -> float:
    return sum(
        binomial_probability(total, i, event_probability)
        for i in range(occurances, total + 1)
    )
