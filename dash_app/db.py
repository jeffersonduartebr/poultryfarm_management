from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Date, Text
import os

def get_engine():
    DB_URL = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:rootpass@mariadb:3306/criacao_aves"
    )
    return create_engine(DB_URL, pool_pre_ping=True)


def init_db(engine):
    metadata = MetaData()

    # Tabela de produção semanal
    Table(
        "producao_aves", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("aviario", String(50)),
        Column("n_aves", Integer),
        Column("peso_medio_chegada", Float),
        Column("uniformidade_chegada", Float),
        Column("semana_idade", Integer),
        Column("aves_na_semana", Integer),
        *[Column(f"mort_d{i}", Integer, default=0) for i in range(1, 8)],
        Column("mort_total", Integer, default=0),
        Column("mort_acum_pct", Float, default=0.0),
        Column("mort_padrao", String(20)),
        Column("data_pesagem", Date),
        Column("peso_med", Float),
        Column("peso_min", Float),
        Column("peso_max", Float),
        Column("consumo_real", Float),
        Column("consumo_padrao", String(20)),
        Column("consumo_acum_real", Float),
        Column("consumo_acum_padrao", String(20)),
    )

    # Tabela de produção diária
    Table(
        "producao_diaria", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("data", Date),
        Column("aviario", String(50)),
        Column("total_birds", Integer),
        Column("total_eggs", Integer),
        Column("pct_production", Float),
    )

    # Registro de camas
    Table(
        "registro_camas", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("date_lot", Date),
        Column("date_implant", Date),
        Column("material", String(100)),
        Column("date_remove", Date),
        Column("treatment", String(100)),
        Column("destination", String(100)),
        Column("contact", String(100)),
    )

    # Inspeção de iscas
    Table(
        "iscas", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("n_isca", Integer),
        Column("produto", String(100)),
        Column("local", String(100)),
        Column("data_vistoria", Date),
        Column("consumida", Integer),
        Column("intacta", Integer),
        Column("mofada", Integer),
        Column("responsavel", String(100)),
    )

    # Registro de visitas
    Table(
        "visitas", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("data", Date),
        Column("objetivo", Text),
        Column("contato", String(50)),
        Column("placa", String(20)),
        Column("assinatura", String(100)),
    )

    # Registro de tratamentos
    Table(
        "tratamentos", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("aviario", String(50)),
        Column("medicacao", String(100)),
        Column("data_inicio", Date),
        Column("data_termino", Date),
        Column("forma_admin", String(50)),
        Column("motivacao", Text),
    )

    # Cria todas as tabelas que não existem
    metadata.create_all(engine)