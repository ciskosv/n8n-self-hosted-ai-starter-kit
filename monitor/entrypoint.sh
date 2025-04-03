#!/bin/bash
set -eu  # Falla si alguna variable no está definida

# Crear sasl_passwd
echo "[${RELAYHOSTIP}]:${MAIL_PORT}    ${ALERTS_ORIGIN_MAIL}:${MAIL_PASSWORD}" > /etc/postfix/sasl_passwd
postmap /etc/postfix/sasl_passwd
chmod 600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db

# Crear generic
echo "root@localhost ${ALERTS_ORIGIN_MAIL}" > /etc/postfix/generic
echo "${ALERTS_ORIGIN_MAIL} ${ALERTS_ORIGIN_MAIL}" >> /etc/postfix/generic
echo "root@${MYHOSTNAME} ${ALERTS_ORIGIN_MAIL}" >> /etc/postfix/generic
postmap /etc/postfix/generic
chmod 600 /etc/postfix/generic /etc/postfix/generic.db

# Crear main.cf
cat <<EOF > /etc/postfix/main.cf
# Básico
myhostname = ${MYHOSTNAME}
mydomain = ${MYDOMAIN}
myorigin = ${MYDOMAIN}
mydestination = localhost

# Relay y Autenticación
relayhost = [${RELAYHOSTIP}]:${MAIL_PORT}
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_sasl_mechanism_filter = plain, login

# TLS
smtp_use_tls = yes
smtp_tls_security_level = encrypt
smtp_tls_wrappermode = yes
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
smtp_tls_CApath=/etc/ssl/certs

# Corrección de Remitentes
sender_canonical_maps = hash:/etc/postfix/generic
smtp_generic_maps = hash:/etc/postfix/generic

# Compatibilidad
compatibility_level = 3.6

# Certificados (opcional para pruebas)
smtpd_tls_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
smtpd_tls_key_file=/etc/ssl/private/ssl-cert-snakeoil.key

# Protocolos
inet_protocols=ipv4

#smtp_enforce_tls = yes

EOF

# Añadimos entrada de IP relayhost a hosts y dns
echo "${RELAYHOSTIP} ${RELAYHOST}" >> /etc/hosts

# Iniciar rsyslog para capturar logs
service rsyslog start

if ! grep -q "${RELAYHOSTIP}" /etc/postfix/sasl_passwd; then
    echo "Error: Credenciales SASL no configuradas correctamente"
    exit 1
fi

# Iniciar postfix
postfix start

cat <<EOF > /shared/scripts/config/ia_stack_monitor_container.conf
[${RELAYHOST}]:${MAIL_PORT} ${ALERTS_ORIGIN_MAIL}:${MAIL_PASSWORD}
ALERT_EMAIL=${ALERT_EMAIL}
ALERTS_ORIGIN_MAIL=${ALERTS_ORIGIN_MAIL}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
MIN_RESPONSE_TIME=${MIN_RESPONSE_TIME}
declare -A SERVICES=(
    ["n8n"]="http://n8n:5678/healthz"
    ["ollama-gpu"]="http://ollama-gpu:11434/api/tags"
    ["whisper-api"]="http://whisper-api:5000/health"
    ["tts-api"]="http://tts-api:5002/health" 
    ["haystack-api"]="http://haystack-api:8000/health"
    ["qdrant"]="http://qdrant:6333/"
    ["ocr-router"]="http://ocr-router:5020/health"
    ["ocr-api"]="http://ocr-api:5003/health"
    ["ocr-paddle"]="http://ocr-paddle:5010/health"
)
MONITOR_INTERVAL=${MONITOR_INTERVAL}
ALERT_GROUPING=${ALERT_GROUPING}
MIN_CRITICAL_ALERTS=${MIN_CRITICAL_ALERTS}
ALERT_THROTTLE_MINUTES=${ALERT_THROTTLE_MINUTES}
TELEGRAM_FORMAT=${TELEGRAM_FORMAT}
ALERT_SEPARATOR=${ALERT_SEPARATOR}
EOF



wait_for_service() {
  local name=$1
  local url=$2
  echo "⏳ Esperando a $name en $url..."
  until curl -sf --max-time 2 "$url" > /dev/null; do
    echo "🔄 $name aún no responde... reintentando..."
    sleep 2
  done
  echo "✅ $name está listo!"
}

# Esperar los servicios definidos
wait_for_service "ocr-api" "http://ocr-api:5003/health"
wait_for_service "ocr-router" "http://ocr-router:5020/health"
wait_for_service "ocr-paddle" "http://ocr-paddle:5010/health"
wait_for_service "n8n" "http://n8n:5678/healthz"
wait_for_service "haystack-api" "http://haystack-api:8000/health"
wait_for_service "whisper-api" "http://whisper-api:5000/health"
wait_for_service "tts-api" "http://tts-api:5002/health"
wait_for_service "ollama-gpu" "http://ollama-gpu:11434/api/tags"
wait_for_service "qdrant" "http://qdrant:6333"


# Esperar un momento para asegurarse de que todo está listo
sleep 2


# Ejecutar el script de monitoreo montado desde el host
bash /shared/scripts/monitor_ia_stack_container.sh