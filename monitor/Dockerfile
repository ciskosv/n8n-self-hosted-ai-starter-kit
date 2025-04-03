FROM debian:bullseye

# Variables de entorno
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Preconfigurar postfix para evitar prompts interactivos
RUN echo "postfix postfix/main_mailer_type string 'Internet Site'" | debconf-set-selections && \
    echo "postfix postfix/mailname string monitor.local" | debconf-set-selections && \
# Instalar paquetes necesarios
    DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y \
    nano \
    postfix \
    rsyslog \
    mailutils \
    bash \
    curl \
    jq \
    bc \
    procps \
    coreutils \
    util-linux \
    docker.io \
    bsdextrautils \
    locales \
    fonts-noto-color-emoji && \
# Configurar idioma
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen && \
# Limpiar
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
