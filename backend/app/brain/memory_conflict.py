from typing import Any


# =====================================================
# OVERWRITE FIELDS
# Бұлар жаңа факт келсе ескісін ауыстырады
# =====================================================

OVERWRITE_FIELDS = {
    "language",
    "age",
    "marital_status",
    "children",
    "career",
    "financial_status",
    "main_goal",
}


# =====================================================
# MERGE FIELDS
# Бұлар тізім ретінде жиналады
# =====================================================

MERGE_FIELDS = {
    "goals",
    "habits",
    "important_events",
}


def normalize_list_value(value: Any) -> list:
    """
    Мәнді list форматына келтіреді.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def merge_unique(
    old_values: list,
    new_values: list
) -> list:
    """
    Duplicate қоспай merge жасайды.
    """

    result = list(old_values)

    for value in new_values:

        if value not in result:
            result.append(value)

    return result


def resolve_memory_update(
    profile,
    memory_data: dict
) -> dict:
    """
    Жаңа memory_data-ны profile-пен салыстырып,
    conflict/update логикасын орындайды.

    Нәтижеде profile.update() үшін дайын dict қайтарады.
    """

    if not memory_data:
        return {}

    resolved = {}

    for key, new_value in memory_data.items():

        if new_value is None:
            continue

        # =============================================
        # 1. OVERWRITE FIELDS
        # =============================================

        if key in OVERWRITE_FIELDS:

            old_value = getattr(
                profile,
                key,
                None
            )

            # Жаңа мән ескіден өзгеше болса —
            # жаңасын қабылдаймыз.
            if new_value != old_value:
                resolved[key] = new_value

            continue

        # =============================================
        # 2. MERGE FIELDS
        # =============================================

        if key in MERGE_FIELDS:

            old_values = normalize_list_value(
                getattr(profile, key, [])
            )

            new_values = normalize_list_value(
                new_value
            )

            merged = merge_unique(
                old_values,
                new_values
            )

            resolved[key] = merged

            continue

        # =============================================
        # 3. БЕЛГІСІЗ FIELD
        # =============================================

        if hasattr(profile, key):
            resolved[key] = new_value

    return resolved