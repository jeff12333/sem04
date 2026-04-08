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
RUN pip install --no-cache-dir flask pandas openpyxl selenium undetected-chromedriver

COPY . .

# 3. Script de inicio mejorado para asegurar que Xvfb esté listo
RUN echo "#!/bin/bash\n\
Xvfb :99 -screen 0 1920x1080x24 &\n\
sleep 3\n\
export DISPLAY=:99\n\
fluxbox &\n\
x11vnc -display :99 -nopw -forever -rfbport 5900 &\n\
sleep 2\n\
python app.py" > /app/start.sh

RUN chmod +x /app/start.sh

# Puerto 5000 (Flask), Puerto 5900 (VNC)
EXPOSE 5000 5900

CMD ["/app/start.sh"]