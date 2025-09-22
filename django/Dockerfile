# Dockerfile
FROM python:3.13.7-slim

# Definir variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 1. Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev librust-gobject-sys-dev weasyprint libcairo2 chromium \
	python3-pip libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libjpeg-dev libopenjp2-7-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Cria diretório da aplicação
WORKDIR /app

# 3. Copia requirements e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia o código da aplicação
COPY . .

# 5. Expõe a porta padrão do Dash
EXPOSE 8050

# 6. Copiar o script de entrada e dar permissão de execução

COPY ../entrypoint.sh /app/entrypoint.sh
RUN chmod +x entrypoint.sh

# Criar um usuário não-root para rodar a aplicação
RUN adduser --disabled-password --gecos "" appuser
USER appuser

#ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["bash", "entrypoint.sh"]
#CMD ["cat", "/app/entrypoint.sh"]
