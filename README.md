# Extractor web de datos hidrometeorológicos de SENAMHI

Aplicación web construida con **FastAPI** para recibir una URL del dominio `senamhi.gob.pe`, rastrear páginas relevantes, extraer datos hidrometeorológicos y devolver un archivo `.zip` con la información organizada en carpetas.

## Qué hace

- Muestra una interfaz web sencilla con una URL precargada.
- Recibe una URL del SENAMHI y valida que pertenezca al dominio permitido.
- Descarga el HTML fuente de la página inicial y de páginas relacionadas.
- Extrae tablas HTML como archivos `.csv`.
- Descarga archivos enlazados (`csv`, `xls`, `xlsx`, `pdf`, `json`, etc.).
- Si detecta contenido dinámico (por ejemplo, páginas con `CSV`, `Buscar` y `Cargando Información...`), usa **Playwright** para renderizar la página, capturar respuestas de red y descargar el CSV cuando exista un botón visible.
- Devuelve al usuario un ZIP con:
  - `pages/`: una carpeta por página procesada.
  - `metadata/manifest.json`: resumen de la ejecución.
  - `tables/`: tablas generadas en CSV.
  - `downloads/`: archivos descargados.
  - `dynamic/network/`: respuestas JSON/CSV/XML capturadas durante la navegación automatizada.

## Estructura del proyecto

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
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Luego abre en tu navegador:

```text
http://127.0.0.1:8000
```

## Uso

1. Pega una URL del SENAMHI.
2. Haz clic en **Extraer y Descargar**.
3. La app descargará automáticamente un ZIP con los resultados.

## Endpoints

### Interfaz web

- `GET /`

### Extracción desde formulario

- `POST /extract`

### Extracción vía API

- `POST /api/extract`

Ejemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.senamhi.gob.pe/main.php?dp=loreto&p=estaciones"}' \
  --output senamhi_export.zip
```

## Recomendaciones prácticas

- Las páginas índice del SENAMHI no siempre contienen datos tabulares directamente; a veces solo enlazan a secciones de monitoreo.
- Varias vistas de monitoreo hidrológico cargan la información de forma dinámica. Por eso el proyecto usa un enfoque híbrido: **HTTPX + BeautifulSoup** para HTML estático y **Playwright** como fallback.
- Conviene agregar **rate limiting**, caché y logs estructurados antes de pasar a producción.
- Si deseas exportar también a Excel, puedes añadir `openpyxl` y generar un `.xlsx` adicional dentro del ZIP.

## Próximas mejoras sugeridas

- Barra de progreso con WebSockets.
- Cola de trabajos para extracciones pesadas.
- Filtros por fecha, hora, región o tipo de estación.
- Persistencia en PostgreSQL o almacenamiento en S3/MinIO.
- Pruebas automatizadas del scraper con respuestas simuladas.

## Nota legal y operativa

Antes de usar el scraper en producción, revisa los términos de uso del sitio, políticas de acceso y límites razonables de consulta. Usa tiempos de espera, reintentos y una frecuencia prudente para evitar sobrecargar el portal.
