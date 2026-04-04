class User:
    """Entidad que representa un usuario del sistema."""

    def __init__(self, id_user: int, name: str, password: str, role: str = None):
        self.id_user = id_user
        self.name = name
        self.password = password
        self.role = role  # 'admin', 'professor', 'student'

    def __repr__(self):
        return f"User(id={self.id_user}, name={self.name}, role={self.role})"
