from evaluation.value_comparator import ValueComparator


def test_numbers_match():
    comparator = ValueComparator()

    assert comparator.compare(354000, 354000.00)


def test_numbers_with_small_difference_match():
    comparator = ValueComparator()

    assert comparator.compare(1000, 1000.5)


def test_numbers_with_large_difference_do_not_match():
    comparator = ValueComparator()

    assert not comparator.compare(1000, 1100)


def test_strings_ignore_whitespace_and_case():
    comparator = ValueComparator()

    assert comparator.compare(
        " ACME Corporation ",
        "acme corporation",
    )


def test_lists_match_recursively():
    comparator = ValueComparator()

    assert comparator.compare(
        ["ACME", 100],
        [" acme ", 100.0],
    )


def test_lists_with_different_length_do_not_match():
    comparator = ValueComparator()

    assert not comparator.compare(
        ["ACME"],
        ["ACME", "Globex"],
    )


def test_nested_objects_match_recursively():
    comparator = ValueComparator()

    assert comparator.compare(
        {
            "vendor": "ACME",
            "amount": 1000,
        },
        {
            "vendor": " acme ",
            "amount": 1000.0,
        },
    )


def test_nested_objects_with_different_keys_do_not_match():
    comparator = ValueComparator()

    assert not comparator.compare(
        {
            "vendor": "ACME",
        },
        {
            "vendor": "ACME",
            "tax": 100,
        },
    )

def test_dates_with_different_formats_match():
    comparator = ValueComparator()

    assert comparator.compare(
        "2026-09-21",
        "21/09/2026",
    )


def test_dates_with_different_separators_match():
    comparator = ValueComparator()

    assert comparator.compare(
        "21-09-2026",
        "2026/09/21",
    )


def test_different_dates_do_not_match():
    comparator = ValueComparator()

    assert not comparator.compare(
        "2026-09-21",
        "22/09/2026",
    )


def test_invalid_dates_fall_back_to_string_comparison():
    comparator = ValueComparator()

    assert comparator.compare(
        "not-a-date",
        "not-a-date",
    )