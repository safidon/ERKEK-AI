"""
ERKEK AI қазақша жауап сапасын тексеру.

Нағыз pipeline (/chat endpoint: memory, категория, қауіп, persona,
жауап стилі) арқылы тұрақты сұрақтар жинағын жіберіп, жауаптарды
Markdown файлға жазады. Уақытша database қолданылады — нағыз
деректерге тимейді. OpenAI кілті backend/.env-тен алынады.

Іске қосу (backend папкасынан):
    python scripts/eval_kazakh.py --model gpt-5.4-mini --label check
    python scripts/eval_kazakh.py --model gpt-5.4-mini --only 1,4,7
"""

import argparse
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

QUESTIONS = [
    # (id, persona, тақырып, хабарлама)
    (1, "brother", "Жұмыс",
     "Сәлем. Жұмысымды ауыстырғым келеді, бірақ қорқамын. Отбасым бар, "
     "айлығым аз. Неден бастаймын?"),
    (2, "strategist", "Қарыз",
     "Үш несием бар, айына 180 мың төлеймін, айлығым 350 мың. "
     "Ақша айдың соңына жетпейді. Не істеуім керек?"),
    (3, "brother", "Ажырасу, балалар",
     "Әйелім екеуміз ажырастық. Екі балам бар, сағынамын. "
     "Бұрынғы әйелім балалармен кездесуге кедергі жасайды."),
    (4, "hardcore", "Тәртіп",
     "Үш айдан бері залға барамын деймін, бірақ бір рет те бармадым. "
     "Ертең бастаймын деп жүре берем."),
    (5, "brother", "Бұрынғы қыз",
     "Бұрынғы қызым екі айдан кейін «қалайсың?» деп жазды. "
     "Жауап берейін бе?"),
    (6, "strategist", "Ақша шешімі",
     "Достарым бәрі жаңа көлік алды. Мен де 8 миллионға несиемен "
     "Camry алсам ба деп отырмын. Айлығым 450 мың."),
    (7, "brother", "Жалғыздық",
     "Соңғы кезде өзімді жалғыз сезінемін. Достарым бар сияқты, "
     "бірақ шын сөйлесетін адам жоқ."),
    (8, "strategist", "Бизнес идея",
     "Кофейня ашқым келеді. 5 миллион жинадым. Тәжірибем жоқ. "
     "Бұл дұрыс идея ма?"),
    (9, "brother", "Жеңіс",
     "Брат, бүгін соңғы несиемді жаптым! 2 жыл төледім. "
     "Енді ешкімге қарызым жоқ."),
    (10, "brother", "Әке және жасөспірім",
     "15 жастағы ұлым менімен сөйлеспейді, тек телефонда отырады. "
     "Қалай жақындасамын?"),
    (11, "hardcore", "Араласқан тіл",
     "Короче брат, жұмыста бастық задолбал уже, постоянно "
     "кричит на меня. Кетіп қалайын ба?"),
    (12, "brother", "Қысқа хабар",
     "Бүгін шаршадым, бірақ залға бардым."),
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", default="low")
    parser.add_argument("--label", default="")
    parser.add_argument(
        "--only",
        default="",
        help="Тек осы сұрақтар, мысалы: 1,4,7",
    )
    parser.add_argument(
        "--out",
        default=str(BACKEND_DIR / "eval_results"),
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # app модульдері import болмай тұрып орнатылады.
    temp_dir = tempfile.mkdtemp(prefix="erkek_eval_")
    os.environ["SQLITE_PATH"] = str(Path(temp_dir) / "eval.db")
    os.environ["DATABASE_URL"] = ""
    os.environ["RATE_LIMIT_ENABLED"] = "false"
    os.environ["DAILY_MESSAGES_PER_USER"] = "100000"
    os.environ["DAILY_SITE_TOKEN_BUDGET"] = "0"
    os.environ["OPENAI_MODEL"] = args.model
    os.environ["OPENAI_REASONING_EFFORT"] = args.effort

    os.chdir(BACKEND_DIR)
    sys.path.insert(0, str(BACKEND_DIR))

    from fastapi.testclient import TestClient

    import app.services.usage as usage
    from app.database import init_database
    from app.main import app
    from app.services.openai_service import FALLBACK_RESPONSES

    init_database()
    client = TestClient(app)

    only = {int(x) for x in args.only.split(",") if x.strip()}
    questions = [q for q in QUESTIONS if not only or q[0] in only]

    fallbacks = set(FALLBACK_RESPONSES.values())
    rows = []

    for qid, persona, topic, message in questions:
        suffix = uuid.uuid4().hex[:8]
        email = f"eval_{suffix}@example.com"
        password = "EvalPassword123!"

        client.post(
            "/auth/register",
            json={
                "accept_terms": True,
                "email": email,
                "username": f"eval_{suffix}",
                "password": password,
            },
        )
        token = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        client.patch(
            "/profile/persona",
            json={"persona": persona},
            headers=headers,
        )
        session_id = client.post(
            "/sessions",
            json={"title": topic},
            headers=headers,
        ).json()["id"]

        tokens_before = usage.site_tokens_used_today()
        started = time.monotonic()

        response = client.post(
            "/chat",
            json={"session_id": session_id, "message": message},
            headers=headers,
        )

        seconds = time.monotonic() - started
        tokens = usage.site_tokens_used_today() - tokens_before

        if response.status_code == 200:
            answer = response.json().get("answer", "")
        else:
            answer = f"[HTTP {response.status_code}] {response.text}"

        failed = answer.strip() in fallbacks or response.status_code != 200

        rows.append(
            (qid, persona, topic, message, answer, seconds, tokens, failed)
        )

        print(
            f"#{qid:>2} {topic:<22} {seconds:5.1f}s "
            f"{tokens:>6} tok{'  FAILED' if failed else ''}",
            flush=True,
        )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    label = f"-{args.label}" if args.label else ""
    out_file = out_dir / f"{args.model}{label}.md"

    total_tokens = sum(r[6] for r in rows)
    total_seconds = sum(r[5] for r in rows)

    lines = [
        f"# {args.model}{label}",
        "",
        f"Reasoning effort: `{args.effort}` · "
        f"сұрақтар: {len(rows)} · "
        f"токен: {total_tokens} · "
        f"уақыт: {total_seconds:.0f} с",
        "",
    ]

    for qid, persona, topic, message, answer, seconds, tokens, failed in rows:
        lines += [
            f"## {qid}. {topic} ({persona})",
            "",
            f"> {message}",
            "",
            f"_{seconds:.1f} с · {tokens} токен"
            f"{' · ҚАТЕ/FALLBACK' if failed else ''}_",
            "",
            answer.strip(),
            "",
            "---",
            "",
        ]

    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved: {out_file}")


if __name__ == "__main__":
    main()
