# 🕒 Configuración de Monitoreo Automático con `crontab` + healthcheck.sh

Este manual te guía para configurar la ejecución automática del script `healthcheck.sh` cada 5 minutos para verificar si tus servicios de IA locales están activos.

---

## ✅ Paso 1: Crear carpeta y mover el script

```bash
mkdir -p ./shared/scripts
mv healthcheck.sh ./shared/scripts/
chmod +x ./shared/scripts/healthcheck.sh
```

---

## ✅ Paso 2: Editar el crontab

Ejecuta:

```bash
crontab -e
```

Y añade la siguiente línea al final (ajusta la ruta según corresponda):

```bash
*/5 * * * * /ruta/absoluta/a/shared/scripts/healthcheck.sh >> /ruta/absoluta/a/logs/healthcheck.log 2>&1
```

🔁 Esto ejecutará el script cada 5 minutos y escribirá los resultados en un archivo `healthcheck.log`.

Puedes verificar que esté activo con:

```bash
crontab -l
```

---

## 🧪 Recomendación adicional

Crea un alias para ejecutar manualmente el script cuando desees:

```bash
alias checkia="bash ./shared/scripts/healthcheck.sh"
```

---

## 📂 Estructura esperada

```
shared/
├── scripts/
│   └── healthcheck.sh
├── logs/
│   └── healthcheck.log (se genera automáticamente)
```

---

## 🔔 Complemento sugerido

Puedes usar este mismo script desde `n8n` para enviar alertas si detecta fallos (ver flujo separado).