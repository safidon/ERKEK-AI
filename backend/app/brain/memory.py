import json
from typing import Optional

from app.database import (
    get_connection,
    adapt_query,
)


class UserProfile:

    # =====================================================
    # MEMORY FIELDS
    # =====================================================

    SCALAR_MEMORY_FIELDS = {
        "age",
        "marital_status",
        "children",
        "career",
        "financial_status",
        "main_goal",
    }

    LIST_MEMORY_FIELDS = {
        "goals",
        "habits",
        "important_events",
    }

    MEMORY_FIELDS = (
        SCALAR_MEMORY_FIELDS
        | LIST_MEMORY_FIELDS
    )

    # =====================================================
    # INIT
    # =====================================================

    def __init__(
        self,
        user_id: str
    ):
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

    # =====================================================
    # UPDATE
    # =====================================================

    def update(
        self,
        **kwargs
    ):
        """
        Профильді жаңартып,
        database-ке сақтайды.

        None мәндерін де қабылдайды.
        Бұл memory field-терді
        толық тазалауға мүмкіндік береді.
        """

        for key, value in kwargs.items():

            if not hasattr(
                self,
                key
            ):
                continue

            if key == "user_id":
                continue

            setattr(
                self,
                key,
                value
            )

        self.save()

    # =====================================================
    # CLEAR ONE MEMORY FIELD
    # =====================================================

    def clear_memory_field(
        self,
        field_name: str
    ) -> bool:
        """
        Бір memory field-ті толық тазартады.
        """

        if (
            field_name
            not in self.MEMORY_FIELDS
        ):
            return False

        if (
            field_name
            in self.LIST_MEMORY_FIELDS
        ):
            setattr(
                self,
                field_name,
                []
            )

        else:
            setattr(
                self,
                field_name,
                None
            )

        self.save()

        return True

    # =====================================================
    # CLEAR ALL MEMORY
    # =====================================================

    def clear_memory(
        self
    ):
        """
        AI сақтаған барлық
        long-term memory-ді тазартады.

        language сақталады.
        """

        self.age = None
        self.marital_status = None
        self.children = None

        self.career = None
        self.financial_status = None
        self.main_goal = None

        self.goals = []
        self.habits = []
        self.important_events = []

        self.save()

    # =====================================================
    # SAVE
    # =====================================================

    def save(
        self
    ):
        """
        UserProfile-ді database-ке сақтайды.

        SQLite және PostgreSQL
        екеуіне де compatible.
        """

        connection = (
            get_connection()
        )

        try:
            cursor = (
                connection.cursor()
            )

            cursor.execute(
                adapt_query(
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
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        CURRENT_TIMESTAMP
                    )

                    ON CONFLICT(user_id)
                    DO UPDATE SET
                        language =
                            excluded.language,

                        age =
                            excluded.age,

                        marital_status =
                            excluded.marital_status,

                        children =
                            excluded.children,

                        career =
                            excluded.career,

                        financial_status =
                            excluded.financial_status,

                        main_goal =
                            excluded.main_goal,

                        goals =
                            excluded.goals,

                        habits =
                            excluded.habits,

                        important_events =
                            excluded.important_events,

                        updated_at =
                            CURRENT_TIMESTAMP
                    """
                ),
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
                    ),
                ),
            )

            connection.commit()

        except Exception:

            connection.rollback()
            raise

        finally:
            connection.close()

    # =====================================================
    # MEMORY CONTEXT
    # =====================================================

    def get_context(
        self
    ) -> str:
        """
        AI prompt-қа берілетін
        long-term memory context.
        """

        context = []

        if self.language:
            context.append(
                f"Тілі: {self.language}"
            )

        if self.age is not None:
            context.append(
                f"Жасы: {self.age}"
            )

        if self.marital_status:
            context.append(
                (
                    "Отбасылық жағдайы: "
                    f"{self.marital_status}"
                )
            )

        if self.children is not None:
            context.append(
                f"Балалары: {self.children}"
            )

        if self.career:
            context.append(
                (
                    "Мансап/жұмыс: "
                    f"{self.career}"
                )
            )

        if self.financial_status:
            context.append(
                (
                    "Қаржылық жағдайы: "
                    f"{self.financial_status}"
                )
            )

        if self.main_goal:
            context.append(
                (
                    "Негізгі мақсаты: "
                    f"{self.main_goal}"
                )
            )

        if self.goals:
            context.append(
                "Мақсаттары: "
                + ", ".join(
                    self.goals
                )
            )

        if self.habits:
            context.append(
                "Әдеттері: "
                + ", ".join(
                    self.habits
                )
            )

        if self.important_events:
            context.append(
                "Маңызды оқиғалар: "
                + ", ".join(
                    self.important_events
                )
            )

        if not context:
            return (
                "Пайдаланушы туралы "
                "сақталған ақпарат жоқ."
            )

        return "\n".join(
            context
        )


# =====================================================
# GET USER PROFILE
# =====================================================

def get_user_profile(
    user_id: str
) -> UserProfile:
    """
    Database-тен пайдаланушы профилін алады.

    Профиль жоқ болса —
    жаңа профиль жасайды.

    SQLite және PostgreSQL compatible.
    """

    profile = UserProfile(
        user_id
    )

    connection = (
        get_connection()
    )

    try:
        cursor = (
            connection.cursor()
        )

        cursor.execute(
            adapt_query(
                """
                SELECT *
                FROM users
                WHERE user_id = ?
                """
            ),
            (
                user_id,
            ),
        )

        row = (
            cursor.fetchone()
        )

        if row is None:
            profile.save()
            return profile

        profile.language = (
            row["language"]
        )

        profile.age = (
            row["age"]
        )

        profile.marital_status = (
            row["marital_status"]
        )

        profile.children = (
            row["children"]
        )

        profile.career = (
            row["career"]
        )

        profile.financial_status = (
            row["financial_status"]
        )

        profile.main_goal = (
            row["main_goal"]
        )

        profile.goals = (
            _load_json_list(
                row["goals"]
            )
        )

        profile.habits = (
            _load_json_list(
                row["habits"]
            )
        )

        profile.important_events = (
            _load_json_list(
                row[
                    "important_events"
                ]
            )
        )

        return profile

    finally:
        connection.close()


# =====================================================
# JSON LIST LOADER
# =====================================================

def _load_json_list(
    value
) -> list[str]:
    """
    Database TEXT/JSON string
    -> Python list[str]
    """

    if not value:
        return []

    # Егер болашақ PostgreSQL schema-да
    # JSON/JSONB қолдансақ, psycopg Python list
    # қайтаруы мүмкін.
    if isinstance(
        value,
        list
    ):
        return [
            str(item)
            for item in value
        ]

    try:
        result = json.loads(
            value
        )

        if isinstance(
            result,
            list
        ):
            return [
                str(item)
                for item in result
            ]

    except (
        json.JSONDecodeError,
        TypeError
    ):
        pass

    return []