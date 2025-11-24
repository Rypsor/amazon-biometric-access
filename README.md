# Control de Acceso Biométrico

Este proyecto es un sistema de control de acceso biométrico basado en la nube que utiliza reconocimiento facial. Permite registrar empleados, verificar su identidad para el acceso a instalaciones y visualizar estadísticas de acceso en tiempo real.

El sistema está construido sobre una arquitectura **Serverless** utilizando servicios de AWS como Lambda, Rekognition, DynamoDB, S3 y API Gateway, con un frontend interactivo desarrollado en **Streamlit**.

## Arquitectura

El siguiente diagrama ilustra el flujo de datos y la arquitectura del sistema:

![Arquitectura del Sistema](readme-images/_Diagrama%20de%20flujo.jpeg)

**Componentes Principales:**
*   **Frontend (Streamlit):** Interfaz de usuario para capturar fotos, registrar empleados y visualizar métricas.
*   **AWS Lambda:**
    *   `access_control_handler`: Procesa las solicitudes de acceso, verifica rostros con Rekognition y registra intentos.
    *   `register_employee`: Gestiona el alta de nuevos empleados en el sistema.
*   **Amazon Rekognition:** Motor de reconocimiento facial.
*   **Amazon DynamoDB:** Base de datos para almacenar metadatos de empleados y logs de acceso.
*   **Amazon S3:** Almacenamiento de fotos de empleados y artefactos de código.
*   **Amazon CloudWatch:** Monitoreo y métricas del sistema.

## Requisitos Previos

Antes de comenzar, asegúrese de tener instalado y configurado lo siguiente:

1.  **Cuenta de AWS:** Necesitará una cuenta de AWS activa con permisos de Administrador para crear recursos (CloudFormation, IAM, S3, Lambda, etc.).
2.  **Python 3.7+:** El proyecto está desarrollado en Python.
3.  **AWS CLI:** La Interfaz de Línea de Comandos de AWS instalada y configurada con sus credenciales (`aws configure`).
4.  **Git:** Para clonar el repositorio.

## Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_DIRECTORIO>
```

### 2. Crear un Entorno Virtual

Es recomendable utilizar un entorno virtual para gestionar las dependencias.

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
.\venv\Scripts\activate
```

### 3. Instalar Dependencias

Instale las librerías necesarias listadas en `requirements.txt`. Además, necesitaremos instalar `pynt` para los scripts de despliegue.

```bash
pip install -r requirements.txt
pip install pynt
```

### 4. Configuración de Parámetros

El sistema utiliza archivos JSON en el directorio `config/` para parametrizar el despliegue.

*   Asegúrese de que existe el archivo `config/biometric-params.json`. Si no existe, puede crearlo copiando `config/biometric-cfn-params.json`:

    ```bash
    cp config/biometric-cfn-params.json config/biometric-params.json
    ```

    Este archivo define el nombre del bucket S3 para los artefactos y las rutas de las funciones Lambda.

    ```json
    {
        "S3BucketNameParameter": "nombre-unico-de-tu-bucket",
        "AccessControlLambdaSourceS3KeyParameter": "src/access_control_handler.zip",
        "RegisterEmployeeLambdaSourceS3KeyParameter": "src/register_employee.zip"
    }
    ```

### 5. Configuración de Credenciales Locales (.env)

Para ejecutar el frontend localmente (`app.py`), cree un archivo `.env` en la raíz del proyecto con sus credenciales de AWS y la URL del API Gateway (que obtendrá después del despliegue).

```env
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_DEFAULT_REGION=us-east-1
API_GATEWAY_URL=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/development
```

> **Nota:** La `API_GATEWAY_URL` se obtendrá tras desplegar la infraestructura.

## Despliegue (Backend)

El proyecto incluye un script de automatización `build.py` que utiliza `pynt` para facilitar el despliegue.

Ejecute los siguientes comandos en orden:

1.  **Limpiar el directorio de construcción:**
    ```bash
    pynt clean
    ```

2.  **Empaquetar las funciones Lambda:**
    Crea los archivos `.zip` necesarios para las funciones.
    ```bash
    pynt packagelambda
    ```

3.  **Subir artefactos a S3:**
    Sube el código de las Lambdas al bucket S3 configurado. Si el bucket no existe, el script intentará crearlo.
    ```bash
    pynt deploylambda
    ```

4.  **Crear el Stack de CloudFormation:**
    Despliega toda la infraestructura en AWS (DynamoDB, Rekognition, API Gateway, etc.).
    ```bash
    pynt createstack
    ```
    *Este proceso puede tomar unos minutos.*

Una vez finalizado `createstack`, vaya a la consola de **AWS CloudFormation**, busque el stack (por defecto `video-analyzer-stack`) y en la pestaña **Outputs** encontrará la URL del API Gateway. Copie esta URL y actualice la variable `API_GATEWAY_URL` en su archivo `.env`.

## Ejecución de la Aplicación (Frontend)

Con la infraestructura desplegada y el archivo `.env` configurado, inicie la aplicación de Streamlit:

```bash
streamlit run app.py
```

Esto abrirá la aplicación en su navegador (usualmente en `http://localhost:8501`).

### Uso de la Aplicación

1.  **Register Employee (Registrar Empleado):**
    *   Seleccione esta opción en la barra lateral.
    *   Ingrese los datos del empleado (Nombre, Apellido, Cédula, Ciudad).
    *   Tome una foto clara del rostro.
    *   Haga clic en "Register Employee".

2.  **Verify Access (Verificar Acceso):**
    *   Seleccione esta opción.
    *   Tome una foto de la persona que desea ingresar.
    *   Haga clic en "Verify Access".
    *   El sistema indicará si el acceso es **Concedido** o **Denegado**.

3.  **Dashboard (Panel de Control):**
    *   Visualice gráficas de intentos de acceso y nuevos registros obtenidas desde CloudWatch.

## Comandos Útiles de Pynt

*   `pynt -l`: Lista todas las tareas disponibles.
*   `pynt stackstatus`: Verifica el estado del stack de CloudFormation.
*   `pynt updatestack`: Actualiza el stack si ha modificado la plantilla de CloudFormation.
*   `pynt deletestack`: Elimina toda la infraestructura creada (¡Cuidado! Esto borrará datos).
*   `pynt deletedata`: Borra los datos de S3 y DynamoDB sin eliminar la infraestructura.
