from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, 
                        String, Float, Date, Text, ForeignKey, Enum)
import os

def get_engine():
    DB_URL = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:rootpass@mariadb:3306/criacao_aves"
    )
    return create_engine(DB_URL, pool_pre_ping=True)

def init_db(engine):
    metadata = MetaData()

    # Tabela Central de Lotes
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
    
    # Tabela de Metas por Linhagem
    Table(
        "metas_linhagem", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("linhagem", String(100), nullable=False),
        Column("semana_idade", Integer, nullable=False),
        Column("peso_medio_g", Float),
        Column("consumo_ave_dia_g", Float),
        Column("consumo_acum_g", Float),
        Column("mortalidade_sem_pct", Float),
        Column("mortalidade_acum_pct", Float)
    )

    # Tabela de produção semanal (Refatorada)
    Table(
        "producao_aves", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("lote_id", Integer, ForeignKey("lotes.id"), nullable=False),
        Column("semana_idade", Integer),
        Column("aves_na_semana", Integer),
        *[Column(f"mort_d{i}", Integer, default=0) for i in range(1, 8)],
        Column("mort_total", Integer, default=0),
        Column("data_pesagem", Date),
        Column("peso_medio", Float),
        Column("consumo_real_ave_dia", Float),
    )

    # Tabela de produção diária de ovos (Refatorada)
    Table(
        "producao_diaria", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("lote_id", Integer, ForeignKey("lotes.id"), nullable=False),
        Column("data", Date),
        Column("total_aves", Integer),
        Column("total_ovos", Integer),
        Column("pct_producao", Float),
    )
    
    # Tabela de Tratamentos (Refatorada)
    Table(
        "tratamentos", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("lote_id", Integer, ForeignKey("lotes.id"), nullable=False),
        Column("medicacao", String(100)),
        Column("data_inicio", Date),
        Column("data_termino", Date),
        Column("periodo_carencia_dias", Integer, default=0),
        Column("forma_admin", String(50)),
        Column("motivacao", Text),
    )

    # Tabela de Custos do Lote
    Table(
        "custos_lote", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("lote_id", Integer, ForeignKey("lotes.id"), nullable=False),
        Column("data", Date),
        Column("tipo_custo", String(100)), # Ex: Ração, Pintinhos, Energia, Mão de Obra
        Column("descricao", Text),
        Column("valor", Float, nullable=False),
    )

    # Tabela de Receitas do Lote
    Table(
        "receitas_lote", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("lote_id", Integer, ForeignKey("lotes.id"), nullable=False),
        Column("data", Date),
        Column("tipo_receita", String(100)), # Ex: Venda de Aves, Venda de Ovos
        Column("descricao", Text),
        Column("valor", Float, nullable=False),
    )

    # Tabelas não associadas a um lote específico (ou associadas de forma flexível)
    Table(
        "registro_camas", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("aviario", String(50)), # Associado ao aviário físico
        Column("date_lot", Date),
        Column("date_implant", Date),
        Column("material", String(100)),
        Column("date_remove", Date),
        Column("treatment", String(100)),
        Column("destination", String(100)),
        Column("contact", String(100)),
    )

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

    Table(
        "visitas", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("data", Date),
        Column("objetivo", Text),
        Column("contato", String(50)),
        Column("placa", String(20)),
        Column("assinatura", String(100)),
    )

    # Cria todas as tabelas que não existem
    metadata.create_all(engine)