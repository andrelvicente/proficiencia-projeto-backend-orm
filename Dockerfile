# Use uma imagem oficial do Python, otimizada para aplicações web
FROM python:3.11-slim-buster

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Adiciona o diretório de trabalho ao PYTHONPATH para que Python encontre os módulos em 'app/'
ENV PYTHONPATH /app

# Copia o arquivo de requisitos para o diretório de trabalho
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da sua aplicação para o diretório de trabalho no container
COPY . .

# Expõe a porta que a aplicação FastAPI vai usar
EXPOSE 8000

# Comando para iniciar a aplicação com Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]