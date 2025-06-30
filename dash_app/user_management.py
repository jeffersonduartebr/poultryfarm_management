import os
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text

def get_engine():
    DB_URL = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:rootpass@mariadb:3306/criacao_aves"
    )
    return create_engine(DB_URL, pool_pre_ping=True)

class User(UserMixin):
    """Classe de usuário para o Flask-Login."""
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password = password_hash

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

def get_user_by_username(username: str) -> User | None:
    """Busca um usuário pelo nome de usuário."""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("SELECT id, username, password_hash FROM usuarios WHERE username = :username")
        result = conn.execute(query, {"username": username}).mappings().first()
        if result:
            return User(id=result['id'], username=result['username'], password_hash=result['password_hash'])
    return None

def get_user_by_id(user_id: int) -> User | None:
    """Busca um usuário pelo ID (usado pelo user_loader do Flask-Login)."""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("SELECT id, username, password_hash FROM usuarios WHERE id = :id")
        result = conn.execute(query, {"id": user_id}).mappings().first()
        if result:
            return User(id=result['id'], username=result['username'], password_hash=result['password_hash'])
    return None

def create_initial_user(username, password):
    """Cria um usuário inicial. Usado por um script separado."""
    engine = get_engine()
    user = User(id=None, username=username, password_hash=None)
    user.set_password(password)

    with engine.connect() as conn:
        with conn.begin():
            existing_user = get_user_by_username(username)
            if existing_user:
                print(f"Usuário '{username}' já existe. Nenhuma ação foi tomada.")
                return

            query = text("INSERT INTO usuarios (username, password_hash) VALUES (:username, :password_hash)")
            conn.execute(query, {"username": user.username, "password_hash": user.password})
            print(f"Usuário '{username}' criado com sucesso.")