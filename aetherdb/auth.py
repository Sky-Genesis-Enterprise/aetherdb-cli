"""
AetherDB authentication module: user creation, login, and password hashing (bcrypt).
"""
from passlib.hash import bcrypt

class User:
    def __init__(self, username: str, password_hash: str, role: str = "user"):
        self.username = username
        self.password_hash = password_hash
        self.role = role  # 'user' or 'admin'

    def verify_password(self, password: str) -> bool:
        if self.password_hash == "":
            return password == ""
        return bcrypt.verify(password, self.password_hash)

class AuthManager:
    def __init__(self):
        self.users = {}  # username -> User

    def add_user(self, username: str, password: str, role: str = "user", password_optional: bool = False):
        if username in self.users:
            raise ValueError("User already exists")
        pw_hash = "" if (password_optional and not password) else bcrypt.hash(password)
        self.users[username] = User(username, pw_hash, role)

    def authenticate(self, username: str, password: str) -> bool:
        user = self.users.get(username)
        if not user:
            return False
        return user.verify_password(password)

    def get_user(self, username: str) -> User:
        return self.users.get(username)

    def change_password(self, username: str, new_password: str):
        user = self.get_user(username)
        if user:
            user.password_hash = bcrypt.hash(new_password)
        else:
            raise ValueError("No such user")

    def set_role(self, acting_user: str, target_user: str, role: str):
        if role not in ("admin", "user", "readonly"):
            raise ValueError("Role must be one of: admin, user, readonly")
        acting = self.get_user(acting_user)
        if not acting or acting.role != "admin":
            raise PermissionError("Only admin can assign roles.")
        target = self.get_user(target_user)
        if not target:
            raise ValueError("No such user")
        target.role = role
