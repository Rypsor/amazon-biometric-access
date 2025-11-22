# Guía de Configuración: Amazon QuickSight para DynamoDB

Esta guía detalla paso a paso cómo conectar tu tabla de DynamoDB `AccessLogs` con Amazon QuickSight para visualizar los datos de acceso biométrico.

## Pre-requisitos

1.  **Cuenta de AWS** con permisos de administrador.
2.  **Tablas DynamoDB** creadas (`AccessLogs` y `employees`).

---

## Estrategia de Conexión

QuickSight no lee DynamoDB directamente de forma nativa. La forma estándar y recomendada por AWS es utilizar **Amazon Athena** como puente.

**Flujo:** DynamoDB -> Conector Athena (Lambda) -> Amazon Athena -> QuickSight

---

## Paso 1: Desplegar el Conector de DynamoDB para Athena

AWS ofrece este conector pre-construido.

1.  Ve a la consola de **AWS Lambda**.
2.  Haz clic en **Create function**.
3.  Selecciona **Browse serverless app repository**.
4.  Busca: `AthenaDynamoDBConnector`.
5.  Selecciona la aplicación publicada por "Amazon Athena Federation".
6.  En la configuración de la aplicación:
    *   **Application name:** `AthenaDynamoDBConnector` (o déjalo por defecto).
    *   **SpillBucket:** Escribe el nombre de un bucket S3 existente (puedes usar el `unrecognized-faces-...` si quieres, o crear uno nuevo llamado `athena-spill-bucket-TU-CUENTA`).
    *   **AthenaCatalogName:** Escribe `dynamodb` (esto será el nombre de la fuente de datos en Athena).
7.  Haz clic en **Deploy**.
    *   *Nota: Esto tardará unos minutos en crear la Lambda necesaria.*

## Paso 2: Configurar Athena

1.  Ve a la consola de **Amazon Athena**.
2.  En el menú izquierdo, ve a **Data sources**.
3.  Haz clic en **Create data source**.
4.  Selecciona **Amazon DynamoDB**. Haz clic en Next.
5.  **Data source name:** Escribe `dynamodb` (debe coincidir con el CatalogName del paso anterior).
6.  **Lambda function:** Selecciona la función que se creó en el Paso 1 (tendrá un nombre largo como `serverlessrepo-AthenaDynamoDBCon-SpillBucket...`).
7.  Haz clic en **Create data source**.

Ahora, en el editor de consultas de Athena:
*   Selecciona **Data source:** `dynamodb`.
*   Deberías ver tus tablas (`AccessLogs`, `employees`) en el panel izquierdo.
*   Ejecuta una consulta de prueba:
    ```sql
    SELECT * FROM "default"."AccessLogs" LIMIT 10;
    ```

## Paso 3: Configurar Amazon QuickSight

Si es tu primera vez en QuickSight, te pedirá crear una cuenta.

1.  Ve a la consola de **QuickSight**.
2.  Si no tienes cuenta, haz clic en **Sign up**.
    *   Selecciona la edición **Standard** o **Enterprise**.
    *   **Importante:** En la pantalla de permisos ("Allow access and autodiscovery for these resources"), asegúrate de marcar:
        *   **Amazon Athena**
        *   **Amazon S3** (Selecciona el bucket que usaste como `SpillBucket` en el paso 1).

### Conectar el Dataset

1.  En QuickSight, ve a **Datasets** -> **New dataset**.
2.  Selecciona **Athena**.
3.  **Data source name:** Escribe `AthenaConnection`. Haz clic en **Create data source**.
4.  **Catalog:** Selecciona `dynamodb`.
5.  **Database:** Selecciona `default`.
6.  **Tables:** Selecciona la tabla `AccessLogs`.
7.  Haz clic en **Select**.
8.  Elige **Directly query your data** (Consultar directamente) o **Import to SPICE** (Importar caché para mayor velocidad).
    *   *Recomendación:* Usa **SPICE** si tienes muchos datos, ya que es más rápido y barato por consulta.
9.  Haz clic en **Visualize**.

## Paso 4: Crear el Dashboard

Ahora estás en el editor de análisis.

1.  **Gráfico de Accesos por Estado:**
    *   En "Visual types", selecciona el gráfico circular (Donut chart).
    *   Arrastra el campo `Status` al apartado **Group/Color**.
    *   Verás la proporción de "Access Granted" vs "Access Denied".

2.  **Línea de Tiempo de Accesos:**
    *   Agrega un nuevo visual (Bar chart o Line chart).
    *   Arrastra `Timestamp` al eje X.
    *   QuickSight agrupará automáticamente por hora/día.

3.  **Tabla de Detalles:**
    *   Selecciona el tipo "Table".
    *   Arrastra `Timestamp`, `EmployeeName`, `Status` y `EmployeeId` a "Value".

¡Listo! Ahora tienes un dashboard conectado a tu base de datos de logs biométricos.
