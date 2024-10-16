# Usar una imagen base de Python 3.9 con ffmpeg ya instalado
FROM python:3.10.4

# Instalar ffmpeg y otras dependencias necesarias
RUN apt-get update && apt-get install -y ffmpeg

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos del proyecto al contenedor
COPY . /app

# Instalar las dependencias del archivo requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar el bot
CMD ["python", "main.py"]
