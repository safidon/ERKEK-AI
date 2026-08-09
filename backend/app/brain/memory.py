import json
from typing import Optional

from app.database import get_connection


class UserProfile:

    def __init__(self, user_id: str):
        self.user_id = user_id

        self.language: Optional[str] = None
        self.age: Optional[int] = None
        self.marital_status: Optional[str] = None
        self.children: Optional[int] = None

        self.career: Optional[str] = None
        self.financial_status: Optional[str] = None
        self.main_goal: Optional[str] = None

        self.goals: list[str] = []
        self.habits: list[str] = []
        self.important_events: list[str] = []

    def update(self, **kwargs):
        """
        Профильді жаңартып, SQLite-ке сақтайды.
        """

        for key, value in kwargs.items():

            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

        self.save()

    def save(self):
        """
        UserProfile-ді SQLite базасына сақтайды.
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO users (
                    user_id,
                    language,
                    age,
                    marital_status,
                    children,
                    career,
                    financial_status,
                    main_goal,
                    goals,
                    habits,
                    important_events,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)

                ON CONFLICT(user_id) DO UPDATE SET
                    language = excluded.language,
                    age = excluded.age,
                    marital_status = excluded.marital_status,
                    children = excluded.children,
                    career = excluded.career,
                    financial_status = excluded.financial_status,
                    main_goal = excluded.main_goal,
                    goals = excluded.goals,
                    habits = excluded.habits,
                    important_events = excluded.important_events,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    self.user_id,
                    self.language,
                    self.age,
                    self.marital_status,
                    self.children,
                    self.career,
                    self.financial_status,
                    self.main_goal,
                    json.dumps(
                        self.goals,
                        ensure_ascii=False
                    ),
                    json.dumps(
                        self.habits,
                        ensure_ascii=False
                    ),
                    json.dumps(
                        self.important_events,
                        ensure_ascii=False
                    )
                )
            )

            connection.commit()

        finally:
            connection.close()

    def get_context(self) -> str:

        context = []

        if self.language:
            context.append(
                f"Тілі: {self.language}"
            )

        if self.age:
            context.append(
                f"Жасы: {self.age}"
            )

        if self.marital_status:
            context.append(
                f"Отбасылық жағдайы: {self.marital_status}"
            )

        if self.children is not None:
            context.append(
                f"Балалары: {self.children}"
            )

        if self.career:
            context.append(
                f"Мансап/жұмыс: {self.career}"
            )

        if self.financial_status:
            context.append(
                f"Қаржылық жағдайы: {self.financial_status}"
            )

        if self.main_goal:
            context.append(
                f"Негізгі мақсаты: {self.main_goal}"
            )

        if self.goals:
            context.append(
                "Мақсаттары: " + ", ".join(self.goals)
            )

        if self.habits:
            context.append(
                "Әдеттері: " + ", ".join(self.habits)
            )

        if self.important_events:
            context.append(
                "Маңызды оқиғалар: "
                + ", ".join(self.important_events)
            )

        if not context:
            return "Пайдаланушы туралы сақталған ақпарат жоқ."

        return "\n".join(context)


def get_user_profile(user_id: str) -> UserProfile:
    """
    SQLite базасынан пайдаланушы профилін алады.

    Егер жоқ болса — жаңа профиль жасайды.
    """

    profile = UserProfile(user_id)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )

        row = cursor.fetchone()

        if row is None:
            profile.save()
            return profile

        profile.language = row["language"]
        profile.age = row["age"]
        profile.marital_status = row["marital_status"]
        profile.children = row["children"]

        profile.career = row["career"]
        profile.financial_status = row["financial_status"]
        profile.main_goal = row["main_goal"]

        profile.goals = _load_json_list(
            row["goals"]
        )

        profile.habits = _load_json_list(
            row["habits"]
        )

        profile.important_events = _load_json_list(
            row["important_events"]
        )

        return profile

    finally:
        connection.close()


def _load_json_list(value) -> list[str]:
    """
    SQLite TEXT -> Python list
    """

    if not value:
        return []

    try:
        result = json.loads(value)

        if isinstance(result, list):
            return result

    except (json.JSONDecodeError, TypeError):
        pass

    return []