# Extractor automatizado de datos hidrometeorológicos de SENAMHI

Aplicación web desarrollada con **FastAPI** que permite ingresar una URL del dominio `senamhi.gob.pe`, rastrear páginas relacionadas, extraer datos hidrometeorológicos y generar un archivo `.zip` con la información organizada de forma estructurada.

## Descripción

Este proyecto automatiza la recolección de información desde páginas del portal del **SENAMHI**. Está diseñado para procesar tanto contenido estático como dinámico, identificar tablas y archivos descargables, y empaquetar todos los resultados en un único archivo comprimido para su posterior análisis o almacenamiento.

## Características principales

- Interfaz web simple e intuitiva con una URL precargada.
- Validación de URLs para asegurar que pertenezcan al dominio permitido: `senamhi.gob.pe`.
- Descarga del HTML fuente de la página principal y de páginas relacionadas.
- Extracción de tablas HTML y conversión a archivos `.csv`.
- Descarga automática de archivos enlazados, incluyendo formatos como:
  - `.csv`
  - `.xls`
  - `.xlsx`
  - `.pdf`
  - `.json`
- Soporte para contenido dinámico mediante **Playwright**.
- Captura de respuestas de red durante la navegación automatizada (`JSON`, `CSV`, `XML`, etc.).
- Generación de un archivo `.zip` con la información organizada por carpetas.

## Estructura de salida

El archivo `.zip` generado incluye una estructura similar a la siguiente:

- `pages/`: contiene una carpeta por cada página procesada.
- `metadata/manifest.json`: resume la ejecución realizada.
- `tables/`: almacena las tablas extraídas en formato `.csv`.
- `downloads/`: incluye los archivos descargados desde los enlaces detectados.
- `dynamic/network/`: guarda respuestas capturadas durante la navegación automatizada.

## Arquitectura del proyecto

```text
senamhi_app/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── utils.py
│   ├── services/
│   │   ├── archive.py
│   │   └── extractor.py
│   ├── static/
│   │   ├── app.js
│   │   └── styles.css
│   └── templates/
│       └── index.html
├── requirements.txt
└── README.md
Tecnologías utilizadas
FastAPI: framework principal para la API y la interfaz web.
HTTPX: cliente HTTP para recuperar contenido estático.
BeautifulSoup: análisis y extracción de contenido HTML.
Playwright: automatización del navegador para renderizar contenido dinámico.
Uvicorn: servidor ASGI para ejecutar la aplicación.
Instalación
1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd senamhi_app
2. Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate
En Windows:
.venv\Scripts\activate
3. Instalar dependencias
pip install -r requirements.txt
4. Instalar Chromium para Playwright
playwright install chromium
Ejecución local
Inicia el servidor con:
uvicorn app.main:app --reload
Luego abre en tu navegador:
http://127.0.0.1:8000
Uso de la aplicación
Ingresa una URL válida del portal de SENAMHI.
Haz clic en Extraer y Descargar.
La aplicación procesará la información disponible.
Al finalizar, se descargará automáticamente un archivo .zip con los resultados.
Endpoints disponibles
Interfaz web
GET /
Extracción desde formulario web
POST /extract
Extracción mediante API
POST /api/extract
Ejemplo de uso con curl
curl -X POST http://127.0.0.1:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.senamhi.gob.pe/main.php?dp=loreto&p=estaciones"}' \
  --output senamhi_export.zip
Funcionamiento general

El sistema utiliza un enfoque híbrido para maximizar la extracción de datos:

Contenido estático: se procesa usando HTTPX y BeautifulSoup.
Contenido dinámico: si la página presenta elementos como botones de búsqueda, mensajes de carga o datos renderizados por JavaScript, se utiliza Playwright para simular la navegación y capturar las respuestas generadas por la página.

Este enfoque permite recuperar información incluso cuando los datos no están disponibles directamente en el HTML inicial.

Consideraciones técnicas
Algunas páginas índice del portal de SENAMHI no contienen datos tabulares directamente, sino enlaces hacia otras secciones.
Varias vistas de monitoreo hidrológico cargan la información de forma dinámica.
El uso de Playwright como mecanismo complementario mejora la cobertura de extracción en escenarios donde el scraping tradicional no es suficiente.
Recomendaciones para producción

Antes de desplegar esta aplicación en un entorno productivo, se recomienda incorporar:

Rate limiting para controlar la frecuencia de solicitudes.
Caché para evitar consultas repetitivas innecesarias.
Logs estructurados para facilitar monitoreo y trazabilidad.
Manejo de errores y reintentos más robusto.
Validaciones adicionales de entrada y salida.
Mejoras futuras
Barra de progreso en tiempo real mediante WebSockets.
Cola de trabajos para extracciones pesadas o concurrentes.
Filtros por fecha, hora, región o tipo de estación.
Persistencia de resultados en PostgreSQL.
Integración con almacenamiento externo como S3 o MinIO.
Pruebas automatizadas del scraper mediante respuestas simuladas.
Exportación adicional a formatos como Excel (.xlsx).
Nota legal y operativa

Antes de utilizar este scraper en producción, es importante revisar los términos de uso del sitio web de SENAMHI, así como sus políticas de acceso y límites razonables de consulta.

Se recomienda implementar tiempos de espera, reintentos controlados y una frecuencia prudente de acceso para evitar sobrecargar el portal o incumplir restricciones del servicio.

Licencia

Este proyecto puede distribuirse bajo la licencia que definas para tu repositorio. Por ejemplo:

MIT License
