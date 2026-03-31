def expected_stat(base, growth, start_level: int, end_level: int, cap) -> int:
    return min(base + (end_level - start_level) * (growth / 100), cap)

def calculate_promoted_stat(base, bonus, cap):
    return min(base + bonus, cap)


#def calculate_percentile(actual, expected, )


def classify_stat(actual, expected, threshold=1.0) -> str:
    diff = actual - expected
    if diff > threshold:
        return "Blessed"
    elif diff < -threshold:
        return "Screwed"
    return "Average"
