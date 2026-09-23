from sqlmodel import Session, create_engine

DATABASE_URL = "sqlite:///./citas.db"

# SQLite necesita esta opción para poder usar la conexión desde FastAPI.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


def get_session():
    """Entrega una sesión de base de datos a cada endpoint."""
    with Session(engine) as session:
        yield session
