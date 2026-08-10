from app.brain.memory import get_user_profile

from app.brain.conversation import (
    add_message,
    get_message_count
)

from app.brain.conversation_sessions import (
    create_session
)

from app.brain.summary_storage import (
    save_summary
)

from app.brain.conversation_archive import (
    archive_summarized_messages,
    get_archive_count,
    get_archived_messages
)


TEST_USER_ID = "pytest_archive_sessions_001"


def prepare_user():
    """
    Test user users кестесінде бар екеніне кепілдік береді.
    """

    get_user_profile(TEST_USER_ID)


def test_archive_isolated_between_sessions():
    """
    Session A архивтелген кезде
    Session B хабарламалары өзгермеуі керек.
    """

    prepare_user()

    # =====================================================
    # 1. ЕКІ SESSION ЖАСАЙМЫЗ
    # =====================================================

    session_a = create_session(
        user_id=TEST_USER_ID,
        title="Archive Session A"
    )

    session_b = create_session(
        user_id=TEST_USER_ID,
        title="Archive Session B"
    )

    session_a_id = session_a["id"]
    session_b_id = session_b["id"]

    # =====================================================
    # 2. SESSION A-ҒА 10 MESSAGE
    # =====================================================

    for index in range(10):

        role = (
            "user"
            if index % 2 == 0
            else "assistant"
        )

        add_message(
            user_id=TEST_USER_ID,
            role=role,
            content=f"Session A message {index + 1}",
            session_id=session_a_id
        )

    # =====================================================
    # 3. SESSION B-ҒА 8 MESSAGE
    # =====================================================

    for index in range(8):

        role = (
            "user"
            if index % 2 == 0
            else "assistant"
        )

        add_message(
            user_id=TEST_USER_ID,
            role=role,
            content=f"Session B message {index + 1}",
            session_id=session_b_id
        )

    # =====================================================
    # 4. БАСТАПҚЫ COUNT
    # =====================================================

    session_a_before = get_message_count(
        user_id=TEST_USER_ID,
        session_id=session_a_id
    )

    session_b_before = get_message_count(
        user_id=TEST_USER_ID,
        session_id=session_b_id
    )

    assert session_a_before == 10
    assert session_b_before == 8

    # =====================================================
    # 5. SESSION A SUMMARY STATE ЖАСАЙМЫЗ
    # =====================================================

    from app.database import get_connection

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT MAX(id) AS latest_id
            FROM conversations
            WHERE user_id = ?
              AND session_id = ?
            """,
            (
                TEST_USER_ID,
                session_a_id
            )
        )

        row = cursor.fetchone()

        latest_a_message_id = int(
            row["latest_id"]
        )

    finally:
        connection.close()

    save_summary(
        user_id=TEST_USER_ID,
        session_id=session_a_id,
        summary="Session A test summary",
        last_message_id=latest_a_message_id
    )

    # =====================================================
    # 6. ТЕК SESSION A ARCHIVE
    # =====================================================

    result = archive_summarized_messages(
        user_id=TEST_USER_ID,
        session_id=session_a_id
    )

    assert result["reason"] == "success"

    # ARCHIVE_KEEP_RECENT = 6
    #
    # Session A = 10 message
    # соңғы 6 active қалады
    # алғашқы 4 archive-ке кетуі керек.

    assert result["archived"] == 4
    assert result["deleted"] == 4

    # =====================================================
    # 7. ACTIVE MESSAGE COUNT
    # =====================================================

    session_a_after = get_message_count(
        user_id=TEST_USER_ID,
        session_id=session_a_id
    )

    session_b_after = get_message_count(
        user_id=TEST_USER_ID,
        session_id=session_b_id
    )

    assert session_a_after == 6

    # Ең маңызды isolation assertion
    assert session_b_after == 8

    # =====================================================
    # 8. ARCHIVE COUNT
    # =====================================================

    archive_a_count = get_archive_count(
        user_id=TEST_USER_ID,
        session_id=session_a_id
    )

    archive_b_count = get_archive_count(
        user_id=TEST_USER_ID,
        session_id=session_b_id
    )

    assert archive_a_count == 4

    # Session B архивтелмеуі керек.
    assert archive_b_count == 0

    # =====================================================
    # 9. ARCHIVED MESSAGE CONTENT
    # =====================================================

    archived_a = get_archived_messages(
        user_id=TEST_USER_ID,
        session_id=session_a_id,
        limit=20
    )

    assert len(archived_a) == 4

    assert all(
        message["session_id"] == session_a_id
        for message in archived_a
    )

    assert all(
        "Session A message" in message["content"]
        for message in archived_a
    )