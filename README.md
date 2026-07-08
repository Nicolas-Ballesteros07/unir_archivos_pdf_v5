# Como ejecutar el proyecto

Aplicacion web en Django para unir PDFs, procesar ZIPs y generar PDFs con nombres personalizados.

## Funcionamiento

1. El usuario entra a una ruta definida en `app/UnificarArchivosPdf/urls.py`.
2. Django redirige la solicitud a la vista correspondiente en `app/UnificarArchivosPdf/views.py`.
3. La vista valida los archivos o datos recibidos.
4. Si hace falta procesar PDFs, ZIP o Excel, la vista llama funciones de `app/UnificarArchivosPdf/utils.py`.
5. La respuesta final puede ser una pagina HTML, un archivo descargable o un mensaje de error.

## Estructura tecnica

| Archivo | Uso |
|---|---|
| `app/UnificarArchivosPdf/urls.py` | Define el enrutamiento de cada endpoint |
| `app/UnificarArchivosPdf/views.py` | Contiene los endpoints y controla la peticion/respuesta |
| `app/UnificarArchivosPdf/utils.py` | Contiene la logica reutilizable y separada por funcion |
| `app/manage.py` | Punto de entrada para ejecutar comandos de Django |

## Endpoints principales

| Ruta | Funcion | Proposito |
| --- | --- | --- |
| `/` | `merge_zip_view` | Pantalla principal para unir PDFs y ZIP |
| `/download-zip-final/` | `download_zip_final` | Descargar el archivo final generado |
| `/merge-excel/` | `merge_excel_view` | Pantalla para unir PDFs con datos de Excel |
| `/generate-named-pdf/<int:record_index>/` | `generate_named_pdf` | Generar el PDF final con nombre personalizado |
| `/health/` | `health_check` | Verificacion de salud del servicio |

## Requisitos

- Python instalado.
- Dependencias instaladas desde `requirements.txt`.
- Se recomienda crear un entorno virtual con Python 3.14.5, que fue la version usada para crear este proyecto.

## Estructura recomendada de ejecucion

### 1. Crear el entorno virtual

Es opcional, pero recomendado para aislar dependencias.

```powershell
python -m venv env
```

### 2. Activar el entorno virtual

```powershell
.\env\Scripts\Activate.ps1
```

### 3. Entrar al proyecto Django

```powershell
cd app
```

### 4. Instalar dependencias

```powershell
pip install -r ..\requirements.txt
```

### 5. Preparar la base de datos y archivos estaticos

```powershell
python manage.py migrate
python manage.py collectstatic --noinput
```

### 6. Ejecutar el servidor

```powershell
python manage.py runserver
```

### 7. Abrir la aplicacion

```text
http://127.0.0.1:8000/
```

## Opcion con script

Tambien existe el script `build.sh`, que ejecuta:

- instalacion de dependencias
- `collectstatic`
- `migrate`

En entornos Unix o Git Bash puedes usarlo como referencia o ejecutarlo con Bash si esta disponible.

## Notas

- El proyecto usa SQLite en `app/db.sqlite3`.
- La variable `SECRET_KEY` se toma desde el entorno.
- Las plantillas estan en `app/templates/` y los archivos estaticos en `app/static/`.
