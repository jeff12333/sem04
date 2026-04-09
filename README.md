Markdown
# 🤖 Bot ONPE - Consulta Electoral Pro

Esta es una aplicación web basada en Flask y Selenium (`undetected-chromedriver`) que automatiza la consulta de miembros de mesa en la plataforma de la ONPE. Está empaquetada en Docker con una interfaz gráfica virtual (Xvfb + VNC) para evadir los bloqueos anti-bots.

## 📁 Estructura del Proyecto

Antes de empezar, asegúrate de que tu carpeta de proyecto (`sem04`) tenga exactamente esta estructura:

```text
/sem04
  ├── app.py
  ├── Dockerfile
  ├── requirements.txt
  └── templates/
      └── index.html
🛠️ Paso 1: Configurar los archivos
1. requirements.txt
Asegúrate de que este archivo contenga exactamente esto:

Plaintext
flask
pandas
openpyxl
selenium
undetected-chromedriver
2. Dockerfile
(Importante: Usa SOLO esta versión, que incluye Xvfb y VNC para evitar errores gráficos)

Dockerfile
FROM python:3.9-slim

# 1. Instalar dependencias del sistema y entorno gráfico
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    x11vnc \
    fluxbox \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Instalar librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copiar el código del proyecto
COPY . .

# 4. Script de inicio para asegurar que Xvfb esté listo
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1920x1080x24 &\n\
sleep 3\n\
export DISPLAY=:99\n\
fluxbox &\n\
x11vnc -display :99 -nopw -forever -rfbport 5900 &\n\
sleep 2\n\
python app.py' > /app/start.sh

RUN chmod +x /app/start.sh

# Puertos: 5000 (Flask) y 5900 (VNC)
EXPOSE 5000 5900

CMD ["/app/start.sh"]
🚀 Paso 2: Instalación y Despliegue
Abre tu terminal en la carpeta del proyecto y ejecuta los siguientes comandos:

1. Limpiar versiones anteriores (opcional pero recomendado):

Bash
docker rm -f onpe-bot
docker system prune -f
2. Construir la imagen de Docker:

Bash
docker build -t onpe-bot .
3. Ejecutar el contenedor:
(Nota: El parámetro --shm-size=2g es obligatorio para que Chrome no colapse por falta de memoria).

Bash
docker run -d \
  -p 5000:5000 \
  -p 5900:5900 \
  --shm-size=2g \
  --name onpe-bot \
  onpe-bot
💻 Paso 3: Uso de la Aplicación
Abre tu navegador web y entra a: http://localhost:5000

Sube tu archivo Excel .xlsx.

Requisito del Excel: Debe tener una columna llamada dni (en minúsculas o mayúsculas).

Espera a que termine. El proceso realiza pausas de 15 a 25 segundos por DNI para simular comportamiento humano y evitar el Error 500. El archivo de resultados se descargará automáticamente.

🕵️‍♂️ (Opcional) Ver al Bot trabajar en vivo
Como el bot se ejecuta dentro de Docker de forma "invisible", puedes conectarte para ver la pantalla virtual:

Descarga e instala un cliente VNC (como VNC Viewer).

Conéctate a la dirección: localhost:5900

¡Verás cómo el navegador se abre y el bot escribe lentamente cada DNI!