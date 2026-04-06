# 🌦️ Extractor automatizado de datos hidrometeorológicos de SENAMHI

Aplicación web desarrollada con **FastAPI** para extraer información hidrometeorológica desde páginas del dominio **SENAMHI** (`senamhi.gob.pe`), procesar contenido estático y dinámico, y generar un archivo `.zip` con los resultados organizados automáticamente.

---

## 📖 Descripción

Este proyecto automatiza la recolección de datos desde el portal de **SENAMHI**, permitiendo rastrear páginas relacionadas, extraer tablas, descargar archivos enlazados y capturar respuestas de red cuando la información se carga dinámicamente.

La aplicación está pensada como una solución práctica para centralizar datos hidrometeorológicos en un formato reutilizable, ordenado y fácil de analizar.

---

## ✨ Características principales

- Interfaz web sencilla e intuitiva.
- Validación de URLs para permitir únicamente enlaces del dominio `senamhi.gob.pe`.
- Descarga del HTML fuente de la página principal y de páginas relacionadas.
- Extracción de tablas HTML y conversión a archivos `.csv`.
- Descarga automática de archivos enlazados, como:
  - `.csv`
  - `.xls`
  - `.xlsx`
  - `.pdf`
  - `.json`
- Soporte para contenido dinámico mediante **Playwright**.
- Captura de respuestas de red durante la navegación automatizada.
- Generación de un archivo `.zip` con toda la información organizada por carpetas.

---

## 🧰 Tecnologías utilizadas

- **FastAPI** — Framework principal para la API y la interfaz web.
- **HTTPX** — Cliente HTTP para obtener contenido estático.
- **BeautifulSoup** — Procesamiento y análisis de HTML.
- **Playwright** — Automatización del navegador para renderizar contenido dinámico.
- **Uvicorn** — Servidor ASGI para ejecutar la aplicación.

---

## 📁 Estructura del proyecto

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

---

## 📦 Estructura de salida

El archivo `.zip` generado contiene una estructura similar a esta:

```text
output.zip
├── pages/
├── metadata/
│   └── manifest.json
├── tables/
├── downloads/
└── dynamic/
    └── network/
```

### Contenido de cada carpeta

- **`pages/`**: guarda una carpeta por cada página procesada.
- **`metadata/manifest.json`**: contiene un resumen de la ejecución.
- **`tables/`**: almacena las tablas extraídas en formato `.csv`.
- **`downloads/`**: incluye los archivos descargados desde los enlaces detectados.
- **`dynamic/network/`**: guarda respuestas capturadas durante la navegación automatizada, como `JSON`, `CSV` o `XML`.

---

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd senamhi_app
```

### 2. Crear y activar el entorno virtual

#### En Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

#### En Windows

```bash
.venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar Chromium para Playwright

```bash
playwright install chromium
```

---

## ▶️ Ejecución local

Inicia el servidor con el siguiente comando:

```bash
uvicorn app.main:app --reload
```

Luego abre en tu navegador:

```text
http://127.0.0.1:8000
```

---

## 🚀 Uso de la aplicación

1. Ingresa una URL válida del portal de **SENAMHI**.
2. Haz clic en **Extraer y Descargar**.
3. La aplicación procesará la página y los recursos relacionados.
4. Al finalizar, se descargará automáticamente un archivo `.zip` con los resultados.

---

## 🔌 Endpoints disponibles

### Interfaz web

```http
GET /
```

### Extracción desde formulario web

```http
POST /extract
```

### Extracción mediante API

```http
POST /api/extract
```

---

## 💻 Ejemplo de uso con `curl`

```bash
curl -X POST http://127.0.0.1:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.senamhi.gob.pe/main.php?dp=loreto&p=estaciones"}' \
  --output senamhi_export.zip
```

---

## 🧠 Funcionamiento general

La aplicación utiliza un enfoque híbrido para maximizar la extracción de datos:

### Contenido estático

Se procesa usando:

- **HTTPX**
- **BeautifulSoup**

Esto permite recuperar el HTML fuente, localizar tablas y detectar archivos enlazados.

### Contenido dinámico

Cuando una página depende de JavaScript para mostrar información, la aplicación utiliza **Playwright** para:

- renderizar la página,
- interactuar con elementos visibles,
- capturar respuestas de red,
- descargar recursos generados dinámicamente.

Este enfoque resulta útil en páginas que muestran mensajes como:

- `CSV`
- `Buscar`
- `Cargando Información...`

---

## 📝 Consideraciones técnicas

- Algunas páginas índice del portal de **SENAMHI** no contienen datos tabulares directamente, sino enlaces a otras secciones.
- Varias vistas de monitoreo hidrológico cargan información de forma dinámica.
- El uso de **Playwright** como complemento del scraping tradicional mejora la cobertura de extracción.

---

## 🛡️ Recomendaciones para producción

Antes de desplegar esta aplicación en un entorno productivo, se recomienda incorporar:

- **rate limiting** para controlar la frecuencia de solicitudes,
- **caché** para evitar consultas repetidas,
- **logs estructurados** para facilitar monitoreo y trazabilidad,
- **manejo de errores y reintentos** más robusto,
- **validaciones adicionales** de entrada y salida.

---

## 🔮 Mejoras futuras

- [ ] Barra de progreso en tiempo real con **WebSockets**
- [ ] Cola de trabajos para extracciones pesadas
- [ ] Filtros por fecha, hora, región o tipo de estación
- [ ] Persistencia en **PostgreSQL**
- [ ] Integración con almacenamiento externo como **S3** o **MinIO**
- [ ] Pruebas automatizadas del scraper
- [ ] Exportación adicional a **Excel (`.xlsx`)**

---

## ⚠️ Nota legal y operativa

Antes de utilizar este scraper en producción, es importante revisar los términos de uso del portal de **SENAMHI**, así como sus políticas de acceso y límites razonables de consulta.

Se recomienda aplicar tiempos de espera, reintentos moderados y una frecuencia prudente de solicitudes para evitar sobrecargar el servicio.

---

## 📄 Licencia

Este proyecto puede distribuirse bajo la licencia que definas para tu repositorio, por ejemplo:

```text
MIT License
```

---

## 👨‍💻 Autor

Proyecto desarrollado para la extracción automatizada de datos hidrometeorológicos desde el portal web de **SENAMHI**.
