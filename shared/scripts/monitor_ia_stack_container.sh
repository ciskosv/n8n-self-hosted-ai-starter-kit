#!/bin/bash
# monitor_ia_stack.sh
# Instala antes las dependencias
# sudo apt update
# sudo apt install docker.io curl jq mailutils bc
#
# Configuración adicional para Telegram:
# Crea un bot de Telegram:
# 
# Habla con @BotFather en Telegram
# 
# Usa el comando /newbot
# 
# Obtendrás un token (ej: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)
# 
# Obtén tu chat_id:
# 
# Envía un mensaje a tu bot
# 
# Visita esta URL en tu navegador (reemplaza TU_TOKEN):
# 
# Copy
# https://api.telegram.org/botTU_TOKEN/getUpdates
# Busca el chat.id en la respuesta JSON
# 
# 
# 🚀 Healthcheck Pro++ para Stack IA con Notificaciones Modulares
VERSION="3.0"

# ========== CONFIGURACIÓN INICIAL ==========
# 1. Definir colores PRIMERO
# Colores ANSI
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
MAGENTA="\033[0;35m"
CYAN="\033[0;36m"
NC="\033[0m"

# 2. Cargar configuración
CONFIG_DIR="/shared/scripts/config"
CONFIG_FILE="$CONFIG_DIR/ia_stack_monitor_container.conf"
# Verificar y cargar configuración
[ ! -f "$CONFIG_FILE" ] && { echo -e "${RED}ERROR: No existe $CONFIG_FILE${NC}"; exit 1; }
source "$CONFIG_FILE" || { echo -e "${RED}ERROR: Fallo al cargar $CONFIG_FILE${NC}"; exit 1; }



# ================= FUNCIONES =================
send_html_email() {
    local subject="$1"
    local html_content="$2"
    local recipient="$ALERT_EMAIL"

    {
        echo "From: Server Monitor <$ALERTS_ORIGIN_MAIL>"
        echo "To: $recipient"
        echo "Subject: $subject"
        echo "MIME-Version: 1.0"
        echo "X-Priority: 1 (Highest)"
        echo "Importance: High"
        echo "Content-Type: text/html; charset=UTF-8"
        echo
        echo "$html_content"
    } | /usr/sbin/sendmail -f $ALERTS_ORIGIN_MAIL -t -oi
}

# Registrar alerta en log persistente
log_alert() {
    local alert_type="$1"
    local message="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] [$alert_type] $message" >> /shared/logs/monitor_alerts.log
}

# Función mejorada para alertas consolidadas
send_consolidated_alert() {
    local alert_messages=$1
    local alert_type=$2
    
    [ -z "$alert_messages" ] && return

    log_alert "$alert_type" "$alert_messages"
    
    # Formatear para Telegram (sin cambios)
    if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
        # Validar formato
        if [[ "$TELEGRAM_FORMAT" != "HTML" && "$TELEGRAM_FORMAT" != "MarkdownV2" ]]; then
            TELEGRAM_FORMAT="HTML"
        fi

        if [ "$DEBUG" = true ]; then
            echo "[DEBUG] Mensaje original:" >> /tmp/monitor_debug.log
            echo "$alert_messages" >> /tmp/monitor_debug.log
        fi

        # Obtener nombre del host en mayúsculas
        local hostname_upper
        hostname_upper=$(hostname | tr '[:lower:]' '[:upper:]')

        # 1. Limpiar mensaje
        local cleaned_message
        cleaned_message=$(echo "$alert_messages" | sed 's/\[.*\] en .*\n//')
        cleaned_message=$(echo "$cleaned_message" | awk '!seen[$0]++')
        
        # Estilo del separador visual (editable en config o arriba del script)
        local separator="${ALERT_SEPARATOR:-━━━━━━━━━━}"  # Usa variable o default

        # Reemplazar <hr> y líneas largas de guiones por el separador dinámico
        cleaned_message="${cleaned_message//<hr>/$'\n'"$separator"$'\n'}"
        cleaned_message=$(echo "$cleaned_message" | sed "s/[-]\{5,\}/$separator/g")

        # 3. Construir mensaje con host + servicios + hora
        local timestamp
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')

        local message_text="<b>⚠️ HOST: ${hostname_upper}</b> 🕒 ${global_time}
${cleaned_message}
"

        # 4. Enviar a Telegram
        local payload
        payload=$(jq -n \
            --arg chat_id "$TELEGRAM_CHAT_ID" \
            --arg text "$message_text" \
            --arg parse_mode "$TELEGRAM_FORMAT" \
            '{chat_id: $chat_id, text: $text, parse_mode: $parse_mode}')

        if [ "$DEBUG" = true ]; then
            echo "[DEBUG] Payload Telegram:" >> /tmp/monitor_debug.log
            echo "$payload" >> /tmp/monitor_debug.log
        fi

        curl -s -X POST \
            -H "Content-Type: application/json" \
            -d "$payload" \
            "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            >> /tmp/monitor_debug.log
    fi

    
    # Enviar correo si está configurado (versión mejorada)
    if [ -n "$ALERT_EMAIL" ]; then
        local subject="[${alert_type}] Alerta de Monitoreo - $(hostname)"
        
        # Procesamiento simplificado y más robusto
        local html_message=$(echo "$alert_messages" | while IFS= read -r line; do
            # Saltar líneas que ya están en el template
            [[ "$line" =~ ^Servidor:|^Fecha:|^Sistema\ de\ Monitoreo ]] && continue
            
            # Conservar líneas divisorias
            [[ "$line" =~ ^--- ]] && echo "<hr>" && continue
            
            # Mantener todo el texto original como HTML seguro
            #echo "<div class='alert-line'>$(echo "$line" | sed 's/&/&amp;/g; s/</&lt;/g; s/>/&gt;/g')</div>"
            echo "<div class='alert-line'>$(echo "$line")</div>"
        done)
        
        # Plantilla HTML más simple y efectiva
        local email_html="<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>${subject}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 650px;
            margin: 0 auto;
            padding: 20px;
        }
        .email-container {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
        }
        .header {
            color: #d9534f;
            font-size: 1.3em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .server-info {
            margin-bottom: 15px;
            font-size: 0.95em;
            color: #555;
        }
        hr {
            border: 0;
            height: 1px;
            background-color: #eee;
            margin: 15px 0;
        }
        .alert-line {
            margin: 8px 0;
            white-space: pre-wrap;
            font-family: monospace;
        }
        .footer {
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #eee;
            font-size: 0.85em;
            color: #777;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class=\"email-container\">
        <div class=\"header\">⚠️ Alerta de Monitoreo: ${alert_type}</div>
        
        <div class=\"server-info\">
            <div><strong>Servidor:</strong> $(hostname)</div>
            <div><strong>Fecha:</strong> $(date '+%Y-%m-%d %H:%M:%S')</div>
        </div>
        
        <hr>
        
        <div class=\"alert-content\">
            ${html_message}
        </div>
        
        <div class=\"footer\">
            <strong>Sistema de Monitoreo IA v${VERSION}</strong><br>
            Mensaje generado automáticamente • $(date '+%Z')
        </div>
    </div>
</body>
</html>"

        send_html_email "$subject" "$email_html"
    fi
}

# Verifica dependencias al inicio
check_dependencies() {
    local missing=()

    # Dependencias base
    local base_cmds=(docker curl awk bc)

    # Dependencias según las opciones habilitadas
    [ -n "$TELEGRAM_BOT_TOKEN" ] && base_cmds+=(jq)
    [ -n "$ALERT_EMAIL" ] && base_cmds+=(mail)

    for cmd in "${base_cmds[@]}"; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}❌ ERROR: Faltan dependencias:${NC} ${missing[*]}"
        echo -e "👉 Puede instalarlas con: ${BLUE}sudo apt install ${missing[*]}${NC}"
        echo -e "📦 O en Dockerfile: ${YELLOW}apt-get install -y ${missing[*]}${NC}"
        exit 1
    fi
}


validate_telegram_config() {
    if [[ -z "$TELEGRAM_BOT_TOKEN" || -z "$TELEGRAM_CHAT_ID" ]]; then
        echo -e "${RED}ERROR: Configuración de Telegram incompleta${NC}"
        echo -e "Se requieren ambas variables: TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID"
        return 1
    fi
    
    # Verificar formato básico del token
    if [[ ! "$TELEGRAM_BOT_TOKEN" =~ ^[0-9]+:[a-zA-Z0-9_-]+$ ]]; then
        echo -e "${RED}ERROR: Formato de token de Telegram inválido${NC}"
        return 1
    fi
    
    return 0
}

# Función para enviar alertas de prueba
test_notifications() {
    local test_type=$1
    local test_message="Mensaje de prueba desde $(hostname) - $(date '+%Y-%m-%d %H:%M:%S')"
    
    case "$test_type" in
        "telegram")
            if [ -n "$TELEGRAM_BOT_TOKEN" ]; then

            # Para la función test_notifications (sección Telegram):
            echo -e "${YELLOW}Enviando mensaje de prueba a Telegram...${NC}"

            # Crear el mensaje con saltos de línea reales (no escapados)
            local test_message="🧪 <b>PRUEBA DE ALERTA</b>
            📱 Mensaje de prueba desde $(hostname)
            ⏰ $(date '+%Y-%m-%d %H:%M:%S')"

            # Usar --raw-input para que jq respete los saltos de línea
            local payload=$(echo "$test_message" | jq -R -s \
                --arg chat_id "$TELEGRAM_CHAT_ID" \
                --arg parse_mode "HTML" \
                '{chat_id: $chat_id, text: ., parse_mode: $parse_mode}')

                local response=$(curl -s -X POST \
                    -H "Content-Type: application/json" \
                    -d "$payload" \
                    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage")
                
                if echo "$response" | jq -e '.ok == true' &>/dev/null; then
                    echo -e "${GREEN}✓ Prueba de Telegram exitosa${NC}"
                else
                    echo -e "${RED}✗ Error en prueba de Telegram:${NC} $(echo "$response" | jq -r '.description // "Error desconocido"')"
                fi
            else
                echo -e "${RED}✗ Telegram no configurado${NC}"
            fi
            ;;
        "email")
            if [ -n "$ALERT_EMAIL" ]; then
                echo -e "${YELLOW}Enviando correo de prueba a $ALERT_EMAIL...${NC}"
                
                echo "Mensaje de prueba desde el script de monitoreo" | mail -s "Alerta de Monitoreo - $(hostname)" "$ALERT_EMAIL"
                
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}✓ Correo enviado (verifica tu bandeja de entrada)${NC}"
                else
                    echo -e "${RED}✗ Error al enviar correo${NC}"
                fi
            else
                echo -e "${RED}✗ Email no configurado${NC}"
            fi
            ;;
        *)
            echo -e "${RED}Tipo de prueba no válido. Usa --test-telegram o --test-email${NC}"
            ;;
    esac
    
    exit 0
}

# Test de conexión y estado
test_connection() {
    local service=$1
    local url=$2
    
    echo -e "${YELLOW}Probando conexión a $service ($url)...${NC}"
    
    # Medir tiempo de respuesta
    local start=$(date +%s.%N)
    local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "ERR")
    local end=$(date +%s.%N)
    local time=$(echo "$end - $start" | bc)
    
    if [[ "$response" =~ ^(200|204|301) ]]; then
        echo -e "${GREEN}✓ Servicio $service accesible - HTTP $response - ${time}s${NC}"
    else
        echo -e "${RED}✗ Error conectando a $service - HTTP $response - ${time}s${NC}"
    fi
}

# Métricas de GPU mejoradas
get_gpu_metrics() {
    if ! command -v nvidia-smi &> /dev/null; then
        echo "${RED}(GPU no disponible)${NC}"
        return
    fi

    local metrics=$(docker exec "$1" nvidia-smi --query-gpu=\
utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw \
--format=csv,noheader,nounits 2>/dev/null)

    # Si falla el comando o no hay salida
    if [ $? -ne 0 ] || [ -z "$metrics" ]; then
        echo "${YELLOW}(Sin datos GPU)${NC}"
        return
    fi

    # Separar y limpiar
    IFS=',' read -r util mem_used mem_total temp power <<< "$metrics"

    # Sustituir N/A o vacíos por guiones
    util="${util//[!0-9]/}"
    mem_used="${mem_used//[!0-9]/}"
    mem_total="${mem_total//[!0-9]/}"
    temp="${temp//[!0-9]/}"
    power="${power//[!0-9]/}"

    util=${util:-0}
    mem_used=${mem_used:-0}
    mem_total=${mem_total:-0}
    temp=${temp:-"–"}
    power=${power:-"–"}

    echo -e "${BLUE}(${util}% GPU  ${mem_used}/${mem_total} MB  ${temp}°C  ${power}W)${NC}"
}


# Tiempo de respuesta HTTP
measure_response() {
    local url=$1
    local start=$(date +%s.%N)
    curl -s -o /dev/null --max-time 2 "$url"
    local end=$(date +%s.%N)
    
    # Usamos awk para cálculo flotante (si bc no está disponible)
    awk "BEGIN {printf \"%.2f\", $end - $start}" 2>/dev/null || echo "0.00"
}

# Estadísticas de contenedor
get_container_stats() {
    if [ -z "$1" ]; then
        echo "(N/D)"
        return
    fi

    local stats=$(docker stats --no-stream --format "{{.CPUPerc}}|{{.MemUsage}}" "$1" 2>/dev/null)
    if [ -z "$stats" ]; then
        echo "(N/D)"
        return
    fi

    echo "$stats" | awk -F'|' '{
        gsub(/%/, "", $1);
        gsub(/\//, " de", $2);
        gsub(/ +/, " ", $2);
        printf "(%.2f%% CPU  %s RAM)", $1, $2
    }'
}


# ================= EJECUCIÓN PRINCIPAL =================

# Procesar argumentos
if [ "$1" = "--test-telegram" ]; then
    test_notifications "telegram"
    exit 0
elif [ "$1" = "--test-email" ]; then
    test_notifications "email"
    exit 0
elif [ "$1" = "--test-connections" ]; then
    for name in "${!SERVICES[@]}"; do
        test_connection "$name" "${SERVICES[$name]}"
    done
    exit 0
fi

check_dependencies

# Reiniciar throttle si es una nueva ejecución
declare -A LAST_ALERT_TIME=()  # <-- Esto siempre limpia el throttle al iniciar
declare -A STATUS_HISTORY

clear
echo -e "${BLUE}
===========================================
  MONITOREO AVANZADO DE STACK IA - v$VERSION
===========================================
${NC}"

echo -e "${MAGENTA}Configuración cargada:${NC}"
echo -e "- Servicios monitoreados: ${#SERVICES[@]}"
echo -e "- Notificaciones: Email ${GREEN}✔${NC} | Telegram $([ -n "$TELEGRAM_BOT_TOKEN" ] && echo "${GREEN}✔${NC}" || echo "${RED}✖${NC}")"
echo -e "- Métricas: GPU ${GREEN}✔${NC} | Docker ${GREEN}✔${NC}"
echo -e "\n${YELLOW}Iniciando monitoreo... (Ctrl+C para salir)${NC}\n"
sleep 2


# Función mejorada para verificar si se debe enviar una alerta (con reset al iniciar)
should_alert() {
    local service=$1
    local current_time=$(date +%s)
    local throttle_seconds=$((ALERT_THROTTLE_MINUTES * 60))
    
    # Al ser inicio de script, siempre alerta
    if [ -z "${LAST_ALERT_TIME[$service]}" ]; then
        LAST_ALERT_TIME[$service]=$current_time
        return 0  # Debe alertar
    fi
    
    # Verificar tiempo desde última alerta
    if (( current_time - ${LAST_ALERT_TIME[$service]} >= throttle_seconds )); then
        LAST_ALERT_TIME[$service]=$current_time
        return 0  # Debe alertar
    fi
    
    return 1  # No alertar (throttled)
}

# Primera ejecución - verificar servicios al inicio
first_run=true

while true; do
    output=""
    critical_alerts=""
    recovery_alerts=""
    any_critical=false
    any_recovery=false
    current_time=$(date +%s)
    
    for name in "${!SERVICES[@]}"; do
        url="${SERVICES[$name]}"
        container_id=$(docker ps --format '{{.ID}} {{.Names}}' | awk -v name="$name" '$2 ~ name { print $1; exit }')
        
        previous_status="${STATUS_HISTORY[$name]}"
       
        # Verificar estado del contenedor
        if [ -z "$container_id" ]; then
            status="${RED}✖ OFFLINE${NC}"
            output+="$(date +'%H:%M:%S') | ${name^^} | ${status}\n"
            
            # Primera ejecución o después del tiempo de throttle
            if [ "$first_run" = true ] || should_alert "$name"; then
                critical_alerts+="<hr>🔴 <b>${name^^}</b> - OFFLINE
🕒 $(date +'%H:%M:%S')"

                any_critical=true
            fi
            
            STATUS_HISTORY[$name]="down"
            continue
        fi

        # Obtener estados
        response_time=$(measure_response "$url")
        http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$url" 2>/dev/null || echo "ERR")

        if [[ "$http_code" =~ ^(200|204|301) ]]; then
            if (( $(echo "$response_time > $MIN_RESPONSE_TIME" | bc -l 2>/dev/null || echo 0) )); then
                status="${YELLOW}⚠ LENTO${NC}"
            else
                status="${GREEN}✔ OPERATIVO${NC}"
            fi
            
            # Información adicional
            extra_info=""
            case "$name" in
                "ollama-gpu") extra_info="(${CYAN}$(get_gpu_metrics "$container_id")${NC})" ;;
                "qdrant")
                    stats=$(get_container_stats "$container_id")
                    
                    # obtenemos versión
                    version=$(curl -s "$url" | jq -r '.version // "N/D"' 2>/dev/null)
                    collection_count=$(curl -s "$url/collections" | jq '.result | length' 2>/dev/null)
                    
                    if [[ "$collection_count" -gt 0 ]]; then
                        collection_info=" - ${YELLOW}${collection_count} collections${NC}"
                    else
                        collection_info=""
                    fi

                    extra_info="(${BLUE}${stats}${NC}${collection_info} - v${version}${NC})"
                    ;;


                *) extra_info="(${BLUE}$(get_container_stats "$container_id")${NC})" ;;
            esac
            
            output+="$(date +'%H:%M:%S') | ${name^^} | ${status} | ${extra_info} | Latencia: ${response_time}s\n"
            
            if [ "$previous_status" = "down" ]; then
                recovery_alerts+="<hr>✅ <b>${name^^}</b> - RECUPERADO
🕒 $(date +'%H:%M:%S')
⏱️ Latencia: ${response_time}s"

                any_recovery=true
            fi
            
            STATUS_HISTORY[$name]="up"
            
        else
            status="${RED}✖ ERROR${NC}"
            message="HTTP $http_code | Latencia: ${response_time}s"
            output+="$(date +'%H:%M:%S') | ${name^^} | ${status} | ${RED}${message}${NC}\n"
            
            # Primera ejecución o después del tiempo de throttle
            if [ "$first_run" = true ] || should_alert "$name"; then
                critical_alerts+="<hr>❌ <b>${name^^}</b> - ERROR
🕒 $(date +'%H:%M:%S')
💻 HTTP $http_code
⏱️ Latencia: ${response_time}s"

                any_critical=true
            fi
            
            STATUS_HISTORY[$name]="down"
        fi
        
    done
    
    # Lógica de notificación mejorada
    # Siempre envía alertas en primera ejecución si hay servicios caídos
    if [ "$first_run" = true ] && [ "$any_critical" = true ]; then
        send_consolidated_alert "$critical_alerts" "CRITICAL"
    elif [ "$any_critical" = true ]; then
        # Fuera de primera ejecución, respeta throttling
        send_consolidated_alert "$critical_alerts" "CRITICAL"
    fi
    
    if [ "$any_recovery" = true ]; then
        send_consolidated_alert "$recovery_alerts" "RECOVERY"
    fi
    
    # Mostrar resultados
    clear
    echo -e "${BLUE}=== ESTADO DEL STACK IA [$(date '+%Y-%m-%d %H:%M:%S')] ===${NC}\n"
    echo -e "$output" | column -t -s'|'
    
    # Resumen corregido
    operativos=0
    advertencias=0
    criticos=0

    for status in "${STATUS_HISTORY[@]}"; do
    case $status in
        "up") ((operativos++)) ;;
        "warn") ((advertencias++)) ;;
        "down") ((criticos++)) ;;
    esac
    done

    echo -e "\n${MAGENTA}Resumen:${NC}"
    echo -e "- ${GREEN}Operativos:${NC} $operativos"
    echo -e "- ${YELLOW}Advertencias:${NC} $advertencias"
    echo -e "- ${RED}Críticos:${NC} $criticos"


    # Ya no es primera ejecución
    first_run=false
    
    sleep $MONITOR_INTERVAL
done