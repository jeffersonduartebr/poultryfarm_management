from sqlalchemy import (create_engine, MetaData, Table, Column, Integer,
                        String, Float, Date, Text, ForeignKey, Enum)
import os

def get_engine():
    """Cria e retorna uma conexão com o banco de dados."""
    DB_URL = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:rootpass@mariadb:3306/criacao_aves"
    )
    return create_engine(DB_URL, pool_pre_ping=True)

def init_db(engine):
    """Define e cria todas as tabelas no banco de dados se não existirem."""
    metadata = MetaData()

    Table(
        "usuarios", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("username", String(80), unique=True, nullable=False),
        Column("password_hash", String(256), nullable=False)
    )

    Table(
        "lotes", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("identificador_lote", String(100), unique=True, nullable=False),
        Column("linhagem", String(100)),
        Column("aviario_alocado", String(50)),
        Column("data_alojamento", Date, nullable=False),
        Column("aves_alojadas", Integer),
        Column("status", Enum('Ativo', 'Finalizado', name='lote_status_enum'), default='Ativo')
    )
    
    Table(
        "metas_linhagem", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("linhagem", String(100), nullable=False),
        Column("semana_idade", Integer, nullable=False),
        Column("peso_medio_g", Float),
        Column("consumo_ave_dia_g", Float),
        Column("consumo_acum_g", Float),
        Column("mortalidade_acum_pct", Float)
    )

    Table(
        "producao_aves", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("lote_id", Integer, ForeignKey("lotes.id", ondelete="CASCADE"), nullable=False),
        Column("semana_idade", Integer),
        Column("aves_na_semana", Integer),
        *[Column(f"mort_d{i}", Integer, default=0) for i in range(1, 8)],
        Column("mort_total", Integer, default=0),
        Column("data_pesagem", Date),
        Column("peso_medio", Float),
        Column("consumo_real_ave_dia", Float),
    )
    
    Table(
        "tratamentos", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("lote_id", Integer, ForeignKey("lotes.id", ondelete="CASCADE"), nullable=False),
        Column("medicacao", String(100)),
        Column("data_inicio", Date),
        Column("data_termino", Date),
        Column("periodo_carencia_dias", Integer, default=0),
        Column("forma_admin", String(50)),
        Column("motivacao", Text),
    )

    Table(
        "custos_lote", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("lote_id", Integer, ForeignKey("lotes.id", ondelete="CASCADE"), nullable=False),
        Column("data", Date),
        Column("tipo_custo", String(100)),
        Column("descricao", Text),
        Column("valor", Float, nullable=False),
    )

    Table(
        "receitas_lote", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("lote_id", Integer, ForeignKey("lotes.id", ondelete="CASCADE"), nullable=False),
        Column("data", Date),
        Column("tipo_receita", String(100)),
        Column("descricao", Text),
        Column("valor", Float, nullable=False),
    )

    metadata.create_all(engine)