from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_id, role, name):
        self.id = int(user_id)
        self.role = role
        self.name = name

    def get_id(self):
        return f"{self.role}:{self.id}"
