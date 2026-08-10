from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Парольді қауіпсіз Argon2 hash түріне айналдырады.
    """

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Кәдімгі парольді сақталған hash-пен салыстырады.
    """

    return password_hash.verify(
        plain_password,
        hashed_password
    )