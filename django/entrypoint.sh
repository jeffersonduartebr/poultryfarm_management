#!/bin/sh

# Coletar arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar o servidor Gunicorn
echo "Iniciando Gunicorn..."
gunicorn gestao_avicultura.wsgi:application --bind 0.0.0.0:8000