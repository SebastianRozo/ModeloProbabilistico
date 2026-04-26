# Cambios en Endpoints de Evaluaciones, Dashboard y Reportes

## Resumen

Se agregaron endpoints para exponer el historial de evaluaciones PHQ-9, estadisticas para el dashboard y reportes filtrables/exportables. Tambien se agrego paginacion a los endpoints GET trabajados.

Por el momento todo se basa solo en PHQ-9. No se implemento GAD-7.

## Endpoints Agregados

### GET /students/{id_estudiante}/evaluations

Devuelve el historial PHQ-9 de un estudiante, su puntaje mas reciente y su riesgo actual.

Query params:

- `page`: pagina actual. Default: `1`.
- `limit`: cantidad de registros por pagina. Default: `10`. Maximo: `100`.

Ejemplo:

```http
GET /students/3/evaluations?page=1&limit=10
```

Respuesta:

```json
{
  "student_id": 3,
  "latest_phq9": {
    "date": "2026-04-26T02:33:29.690913+00:00",
    "test_name": "PHQ-9",
    "score": 10,
    "risk": "moderado"
  },
  "current_risk": "moderado",
  "history": [
    {
      "date": "2026-04-26T02:33:29.690913+00:00",
      "test_name": "PHQ-9",
      "score": 10,
      "risk": "moderado"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

Uso frontend:

- Grafico de evolucion de riesgo por estudiante.
- Tabla de historial de pruebas.
- Card de puntaje/riesgo actual.

### GET /dashboard/stats

Devuelve estadisticas generales para el dashboard.

Query params:

- `page`: pagina actual para la evolucion mensual. Default: `1`.
- `limit`: cantidad de meses por pagina. Default: `12`. Maximo: `60`.

Ejemplo:

```http
GET /dashboard/stats?page=1&limit=12
```

Respuesta:

```json
{
  "risk_distribution": {
    "riesgo_bajo": 1,
    "riesgo_medio": 1,
    "riesgo_alto": 0
  },
  "monthly_evolution": [
    {
      "mes": "Abril",
      "anio": 2026,
      "riesgo_promedio": 24.44,
      "puntaje_promedio": 6.6
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 12,
    "total": 1,
    "total_pages": 1
  }
}
```

Uso frontend:

- `risk_distribution`: grafico circular.
- `monthly_evolution`: grafico de barras.
- `riesgo_promedio`: porcentaje calculado sobre el maximo PHQ-9, es decir `puntaje_promedio / 27 * 100`.
- `puntaje_promedio`: puntaje promedio real PHQ-9 del mes.

### GET /evaluations

Devuelve una lista de estudiantes con su riesgo actual y la fecha de su ultima prueba PHQ-9.

Query params:

- `risk`: filtro opcional por riesgo. Acepta `bajo`, `medio`, `alto`, `riesgo_bajo`, `riesgo_medio`, `riesgo_alto`.
- `page`: pagina actual. Default: `1`.
- `limit`: cantidad de registros por pagina. Default: `10`. Maximo: `100`.

Ejemplo:

```http
GET /evaluations?risk=medio&page=1&limit=10
```

Respuesta:

```json
{
  "items": [
    {
      "student_id": 3,
      "student_code": "0222013002",
      "name": "luis",
      "last_name": "vergel",
      "email": "luisverlet@gmail.com",
      "semester": 1,
      "gender": "Male",
      "faculty": "Ingenieria",
      "program": "ingenieria de sistemas",
      "latest_phq9_score": 10,
      "last_evaluation_date": "2026-04-26T02:33:29.690913+00:00",
      "current_risk": "riesgo_medio"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  },
  "filters": {
    "risk": "riesgo_medio"
  }
}
```

Uso frontend:

- Tabla de reportes.
- Filtro por riesgo alto, medio o bajo.
- Visualizacion de ultima prueba hecha por estudiante.

### GET /reports/export

Exporta el reporte de evaluaciones en formato PDF.

Query params:

- `risk`: filtro opcional por riesgo. Acepta `bajo`, `medio`, `alto`, `riesgo_bajo`, `riesgo_medio`, `riesgo_alto`.
- `page`: pagina actual. Default: `1`.
- `limit`: cantidad de registros exportados. Default: `100`. Maximo: `1000`.

Ejemplo:

```http
GET /reports/export?risk=alto&page=1&limit=100
```

Respuesta:

```text
Content-Type: application/pdf
Content-Disposition: attachment; filename=reporte_evaluaciones.pdf
```

Contenido del PDF:

- Titulo del reporte.
- Fecha de generacion.
- Filtro de riesgo aplicado.
- Pagina exportada y total de registros.
- Resumen del modulo.
- Tabla estilizada con colores por nivel de riesgo.
- Datos del estudiante, puntaje PHQ-9, fecha de ultima prueba y riesgo actual.

## Endpoints Cambiados

### GET /students

Antes devolvia directamente todos los estudiantes.

Ahora usa paginacion:

```http
GET /students?page=1&limit=10
```

Respuesta actual:

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 0,
    "total_pages": 0
  }
}
```

Uso frontend:

- El total de alumnos ahora se debe leer desde `pagination.total`.
- La lista de alumnos esta en `items`.

### POST /predict

Se mantiene funcionando como antes, pero ahora antes de guardar una respuesta PHQ-9 asegura que exista la columna `created_at` en la tabla `phq9_responses`.

Esto permite que las respuestas nuevas queden con fecha y puedan aparecer correctamente en historial, reportes y graficos.

## Cambios en Base de Datos

Se agrego la columna `created_at` a `phq9_responses`:

```sql
ALTER TABLE phq9_responses
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
```

Tambien se declaro en el modelo SQLAlchemy `PHQ9Response`.

## Calculo de Riesgo

### Riesgo detallado PHQ-9

Usado en historial individual:

- `0-4`: `minimo`
- `5-9`: `leve`
- `10-14`: `moderado`
- `15-19`: `moderadamente_severo`
- `20-27`: `severo`

### Grupo de riesgo para dashboard/reportes

Usado en graficas y filtros:

- `0-9`: `riesgo_bajo`
- `10-14`: `riesgo_medio`
- `15-27`: `riesgo_alto`

## Archivos Modificados

- `api/main.py`
- `services/model/main.py`
- `services/auth/main.py`
- `db/models/forms/main.py`
- `requirements.txt`

## Archivo Agregado

- `CAMBIOS_ENDPOINTS_DASHBOARD_REPORTES.md`

## Verificaciones Realizadas

Se verifico compilacion del backend:

```bash
python -m compileall api services db
```

Se verifico que la API importe correctamente desde el entorno virtual:

```bash
.venv/Scripts/python.exe -c "from api.main import app; print('api import ok')"
```

Se probaron consultas principales contra la base de datos:

- Estadisticas del dashboard.
- Reporte de evaluaciones con filtro de riesgo.
- Exportacion PDF.
- Listado paginado de estudiantes.

## Dependencia Agregada

Para generar PDFs se agrego:

```text
reportlab>=4.0,<5.0
```
