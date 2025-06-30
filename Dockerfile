# Dockerfile
FROM python:3.11-slim

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

# 6. Comando de inicialização
CMD ["python", "app.py"]
