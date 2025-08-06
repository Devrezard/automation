# Utiliser une image Python officielle comme base
FROM python:3.12-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libffi-dev \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    libpng16-16 \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Générer la locale française UTF-8
RUN sed -i '/fr_FR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

ENV LANG=fr_FR.UTF-8
ENV LANGUAGE=fr_FR:fr
ENV LC_ALL=fr_FR.UTF-8

# Copier les fichiers de dépendances
COPY requirements.txt pyproject.toml ./

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source de l'application
COPY main.py ./

# Exposer le port sur lequel Streamlit s'exécute
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Commande pour démarrer l'application
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]