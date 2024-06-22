# Manual de Despliegue de MovieSphere

Este manual de despliegue proporciona instrucciones paso a paso para poner en marcha la aplicación MovieSphere. Está contenida en un único repositorio, por lo que el proceso de despliegue es sencillo e implica clonar el repositorio, instalar las dependencias y ejecutar el servidor.

## Prerrequisitos

Antes de comenzar con el despliegue, se deben tener instalados los siguientes componentes en el sistema:

- **Python 3.11.9**: Para verificar la versión de Python hay que ejecutar `python --version` en la terminal.
- **Git**: Para verificar la instalación de Git hay que ejecutar `git --version` en la terminal.
- **Virtualenv (opcional)**: Se recomienda usar un entorno virtual para gestionar las dependencias de Python. Para instalar virtualenv puede ejecutar `pip install virtualenv`.

## Pasos para el Despliegue

### Paso 1: Clonar el Repositorio

1. Abra una terminal y ejecute el siguiente comando para clonar el repositorio de la aplicación:
    ```sh
    git clone https://github.com/GII-IS-TFG-framonmar7/MovieSphere.git
    ```

2. Cambie al directorio del repositorio clonado:
    ```sh
    cd MovieSphere
    ```

### Paso 2: Crear y Activar un Entorno Virtual (Opcional)

Se recomienda crear un entorno virtual para aislar las dependencias de la aplicación. Para crear y activar un entorno virtual, ejecute los siguientes comandos:

- En sistemas Windows:
    ```sh
    python -m venv ..\env
    ..\env\Scripts\activate
    ```
    
- En sistemas Unix o MacOS:
    ```sh
    python3 -m venv ../env
    source ../env/bin/activate
    ```

### Paso 3: Instalar las Dependencias

Con el entorno virtual activado (si se utiliza), instale las dependencias requeridas por la aplicación ejecutando:
    ```sh
    pip install -r requirements.txt
    ```

### Paso 4: Crear Archivo .env en el Directorio Principal

En el directorio principal del proyecto (`moviesphere`), cree un archivo `.env` con el siguiente contenido:
    ```env
    EMAIL_HOST_USER=movie.sphere.communications@gmail.com
    EMAIL_HOST_PASSWORD=MOVIESPHERE_PASSWORD
    ```

### Paso 5: Migrar la Base de Datos

Ejecute las migraciones de la base de datos para crear las tablas necesarias:
    ```sh
    python manage.py makemigrations
    python manage.py migrate
    ```

### Paso 6: Descargar Pesos del Modelo YOLO

Descargue los pesos del modelo YOLO ejecutando el siguiente comando:
    ```sh
    python manage.py get_weights
    ```

### Paso 7: Poblar la Base de Datos

Ejecute el script de inicialización para poblar la base de datos con los datos iniciales:
    ```sh
    python manage.py initial_data
    ```

### Paso 8: Ejecutar el Servidor de Desarrollo

Finalmente, ejecute el servidor de desarrollo de Django:
    ```sh
    python manage.py runserver
    ```

Abra su navegador web y navegue a [http://127.0.0.1:8000/](http://127.0.0.1:8000/) para ver la aplicación en funcionamiento.