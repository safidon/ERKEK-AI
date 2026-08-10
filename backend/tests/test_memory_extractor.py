from app.brain.memory_extractor import extract_memory


def test_age_kz():
    result = extract_memory(
        "Мен 32 жастамын."
    )

    assert result["age"] == 32


def test_children_kz():
    result = extract_memory(
        "Менің екі балам бар."
    )

    assert result["children"] == 2


def test_children_ru():
    result = extract_memory(
        "У меня двое детей."
    )

    assert result["children"] == 2


def test_new_job():
    result = extract_memory(
        "Жаңа тұрақты жұмыс таптым."
    )

    assert result["career"] == "тұрақты жұмысы бар"


def test_unemployed():
    result = extract_memory(
        "Жұмыстан шығып қалдым."
    )

    assert result["career"] == "жұмыссыз"


def test_finance():
    result = extract_memory(
        "Менің қарызым бар."
    )

    assert result["financial_status"] == "қарызы/несиесі бар"


def test_goal():
    result = extract_memory(
        "Хочу купить квартиру."
    )

    assert result["main_goal"] == "үй/пәтер алу"