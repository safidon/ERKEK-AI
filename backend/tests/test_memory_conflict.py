from app.brain.memory import get_user_profile
from app.brain.memory_conflict import resolve_memory_update


def test_career_conflict_update():
    user_id = "pytest_memory_conflict_001"

    profile = get_user_profile(user_id)

    profile.update(
        career="жұмысы тұрақсыз"
    )

    resolved = resolve_memory_update(
        profile,
        {
            "career": "тұрақты жұмысы бар"
        }
    )

    assert resolved["career"] == "тұрақты жұмысы бар"


def test_goals_merge_without_duplicates():
    user_id = "pytest_memory_conflict_002"

    profile = get_user_profile(user_id)

    profile.update(
        goals=["тұрақты жұмыс табу"]
    )

    resolved = resolve_memory_update(
        profile,
        {
            "goals": [
                "тұрақты жұмыс табу",
                "үй алу"
            ]
        }
    )

    assert "тұрақты жұмыс табу" in resolved["goals"]
    assert "үй алу" in resolved["goals"]
    assert resolved["goals"].count("тұрақты жұмыс табу") == 1