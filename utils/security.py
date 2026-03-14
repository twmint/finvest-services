from pwdlib import PasswordHash

pwd_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_hasher.verify(plain, hashed)
