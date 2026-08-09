class CurrentContext:

    def __init__(self):
        self.current_problem = None
        self.emotion = None
        self.risk = None
        self.category = None
        self.language = None

    def update(
        self,
        current_problem=None,
        emotion=None,
        risk=None,
        category=None,
        language=None
    ):
        if current_problem is not None:
            self.current_problem = current_problem

        if emotion is not None:
            self.emotion = emotion

        if risk is not None:
            self.risk = risk

        if category is not None:
            self.category = category

        if language is not None:
            self.language = language

    def get_context(self) -> str:

        context = []

        if self.current_problem:
            context.append(
                f"Қазіргі мәселесі: {self.current_problem}"
            )

        if self.emotion is not None:
            context.append(
                f"Эмоциялық жағдайы: {self.emotion}"
            )

        if self.risk:
            context.append(
                f"Тәуекел деңгейі: {self.risk}"
            )

        if self.category:
            context.append(
                f"Категориясы: {self.category}"
            )

        if self.language:
            context.append(
                f"Тілі: {self.language}"
            )

        if not context:
            return "Қазіргі контекст туралы ақпарат жоқ."

        return "\n".join(context)


CURRENT_CONTEXTS: dict[str, CurrentContext] = {}


def get_current_context(user_id: str) -> CurrentContext:

    if user_id not in CURRENT_CONTEXTS:
        CURRENT_CONTEXTS[user_id] = CurrentContext()

    return CURRENT_CONTEXTS[user_id]