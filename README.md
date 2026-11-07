# Proyecto Cafetería - Pastelería

**Autor:** Roberto Ángel

Aplicación web con Flask-AppBuilder y MySQL para gestionar una cafetería: productos, recetas con costos, clientes, ventas, reportes y un asistente con inteligencia artificial.

## Funcionalidades

- **Inventario:** categorías, productos, ingredientes y recetas. El costo de cada producto se calcula a partir de sus ingredientes.
- **Ventas:** registro de una venta en una sola pantalla. Se busca al cliente por carnet (CI/NIT) o por nombre, o se registra un cliente nuevo junto con la venta.
- **Reportes con filtros:**
  - Ventas por período (fechas y método de pago)
  - Productos más vendidos (fechas y categoría)
  - Ganancia por producto (fechas y categoría)
- **Asistente IA:** sugiere precios y responde preguntas sobre el negocio (API de Groq).
- **Seguridad:** inicio de sesión, roles y permisos de Flask-AppBuilder, y protección CSRF.

## Tablas

`categorias`, `productos`, `ingredientes`, `recetas`, `clientes`, `ventas`, `detalle_ventas`

## Tecnologías

Python 3, Flask-AppBuilder 5.3, MySQL (XAMPP), PyMySQL, Bootstrap 3.

## Instalación

1. Encender **MySQL** en XAMPP y crear la base de datos `cafeteria_db`.
2. Crear el entorno virtual e instalar las dependencias:

   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copiar `.env.example` como `.env` y completar los valores (la clave de la IA es opcional).
4. Crear las tablas:

   ```cmd
   python init_db.py
   ```

5. Crear el usuario administrador:

   ```cmd
   set FLASK_APP=app
   flask fab create-admin
   ```

6. Ejecutar la aplicación:

   ```cmd
   python run.py
   ```

   Abrir http://127.0.0.1:5000 e iniciar sesión.

## Estructura

```
app/
  models.py      modelos (tablas)
  views.py       CRUD y menús
  pantallas.py   nueva venta, recetas y asistente IA
  reportes.py    los 3 reportes
  ia.py          conexión con la IA
  templates/     páginas HTML
  static/        estilos
config.py        configuración
init_db.py       crea las tablas
run.py           inicia la aplicación
```
