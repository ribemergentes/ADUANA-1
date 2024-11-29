

from flask import Flask, render_template, request, redirect, url_for, session, Response
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import pandas as pd
from io import BytesIO
from flask import Response, send_file
from flask import send_from_directory
from werkzeug.utils import secure_filename
import os
from werkzeug.security import generate_password_hash, check_password_hash
from io import StringIO, BytesIO
from datetime import datetime
import sqlite3
import csv
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter, portrait
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "admin"

# Función para inicializar la base de datos


def init_db():
    conn = sqlite3.connect("plataforma.db")
    cursor = conn.cursor()

    # Crear tablas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_completo TEXT NOT NULL,
        correo TEXT NOT NULL UNIQUE,
        contrasena TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operaciones (
        id_operacion INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT DEFAULT 'pendiente',
        fecha TEXT,
        id_cotizacion INTEGER,
        id_usuario INTEGER,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documentos (
        id_documento INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_archivo TEXT NOT NULL,
        url_archivo TEXT NOT NULL,
        id_operacion INTEGER,
        fecha_subida TEXT DEFAULT CURRENT_DATE,
        FOREIGN KEY (id_operacion) REFERENCES operaciones(id_operacion)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cotizaciones (
        id_cotizacion INTEGER PRIMARY KEY AUTOINCREMENT,
        producto TEXT NOT NULL,
        pais_origen TEXT NOT NULL,
        peso REAL NOT NULL,
        dimensiones TEXT,
        costo_total REAL,
        valor_declarado REAL NOT NULL,
        id_usuario INTEGER,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    )
    """)
    conn.commit()
    conn.close()


# Inicializar la base de datos al iniciar la app
init_db()

# Ruta de inicio de sesión


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        conn = sqlite3.connect("plataforma.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE correo = ?", (correo,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario[3], contrasena):
            session['user_id'] = usuario[0]
            session['user_name'] = usuario[1]
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Credenciales inválidas")
    return render_template("login.html")

# Ruta del Dashboard


@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect("/")
    return render_template("dashboard.html", nombre=session['user_name'])

# Ruta para cerrar sesión


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Rutas para Usuarios








@app.route("/usuarios")
def usuarios():
    if 'user_id' not in session:
        return redirect("/")
    conn = sqlite3.connect("plataforma.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template("usuarios/index.html", usuarios=usuarios)


@app.route("/usuarios/create")
def usuarios_create():
    return render_template("usuarios/create.html")


@app.route("/usuarios/save", methods=["POST"])
def usuarios_save():
    nombre = request.form['nombre_completo']
    correo = request.form['correo']
    contrasena = generate_password_hash(request.form['contrasena'])

    conn = sqlite3.connect("plataforma.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO usuarios (nombre_completo, correo, contrasena) VALUES (?, ?, ?)",
                   (nombre, correo, contrasena))
    conn.commit()
    conn.close()
    return redirect("/usuarios")

# Rutas para Operaciones


# @app.route("/operaciones")
# def operaciones():
#     if 'user_id' not in session:
#         return redirect("/")

#     estado_filtro = request.args.get("estado", "all")
#     fecha_filtro = request.args.get("fecha", "")

#     conn = sqlite3.connect("plataforma.db")
#     conn.row_factory = sqlite3.Row
#     cursor = conn.cursor()

#     # Base de la consulta
#     query = "SELECT * FROM operaciones WHERE id_usuario = ?"
#     params = [session["user_id"]]

#     # Agregar filtro por estado
#     if estado_filtro != "all":
#         query += " AND estado = ?"
#         params.append(estado_filtro)

#     # Agregar filtro por fecha
#     if fecha_filtro:
#         query += " AND fecha = ?"
#         params.append(fecha_filtro)

#     cursor.execute(query, params)
#     operaciones = cursor.fetchall()
#     conn.close()

#     # Pasar los filtros al template para mantener los valores seleccionados
#     return render_template("operaciones/index.html", operaciones=operaciones, estado_filtro=estado_filtro, fecha_filtro=fecha_filtro)

@app.route("/operaciones")
def operaciones():
    if 'user_id' not in session:
        return redirect("/")

    # Obtener filtros y parámetros de paginación
    estado_filtro = request.args.get("estado", "all")
    fecha_filtro = request.args.get("fecha", "")
    pagina = int(request.args.get("pagina", 1))
    resultados_por_pagina = 10
    offset = (pagina - 1) * resultados_por_pagina

    conn = sqlite3.connect("plataforma.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Base de la consulta
    query = "SELECT * FROM operaciones WHERE id_usuario = ?"
    params = [session["user_id"]]

    # Agregar filtro por estado
    if estado_filtro != "all":
        query += " AND estado = ?"
        params.append(estado_filtro)

    # Agregar filtro por fecha
    if fecha_filtro:
        query += " AND fecha = ?"
        params.append(fecha_filtro)

    # Contar el total de resultados
    total_query = f"SELECT COUNT(*) FROM ({query})"
    cursor.execute(total_query, params)
    total_resultados = cursor.fetchone()[0]

    # Aplicar paginación
    query += " LIMIT ? OFFSET ?"
    params.extend([resultados_por_pagina, offset])

    cursor.execute(query, params)
    operaciones = cursor.fetchall()
    conn.close()

    # Calcular el número total de páginas
    total_paginas = (total_resultados + resultados_por_pagina -
                     1) // resultados_por_pagina

    return render_template(
        "operaciones/index.html",
        operaciones=operaciones,
        estado_filtro=estado_filtro,
        fecha_filtro=fecha_filtro,
        pagina=pagina,
        total_paginas=total_paginas,
    )


@app.route("/operaciones/exportar")
def exportar_operaciones():
    if 'user_id' not in session:
        return redirect("/")

    # Obtener filtros y formato solicitado
    estado_filtro = request.args.get("estado", "all")
    fecha_filtro = request.args.get("fecha", "")
    formato = request.args.get("formato", "csv").lower()  # Asegurar minúsculas

    if formato not in ["csv", "xlsx", "pdf"]:
        return "Formato no soportado", 400

    conn = sqlite3.connect("plataforma.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Base de la consulta
    query = "SELECT * FROM operaciones WHERE id_usuario = ?"
    params = [session["user_id"]]

    if estado_filtro != "all":
        query += " AND estado = ?"
        params.append(estado_filtro)

    if fecha_filtro:
        query += " AND fecha = ?"
        params.append(fecha_filtro)

    cursor.execute(query, params)
    operaciones = cursor.fetchall()
    conn.close()

    # Exportación CSV
    if formato == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID Operación", "Descripción", "Estado", "Fecha"])
        for operacion in operaciones:
            writer.writerow([operacion["id_operacion"], operacion["descripcion"],
                            operacion["estado"], operacion["fecha"]])
        output.seek(0)
        return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=operaciones.csv"})

    # Exportación Excel
    if formato == "xlsx":
        output = BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Operaciones"
        ws.append(["ID Operación", "Descripción", "Estado", "Fecha"])
        for operacion in operaciones:
            ws.append([operacion["id_operacion"], operacion["descripcion"],
                      operacion["estado"], operacion["fecha"]])
        wb.save(output)
        output.seek(0)
        return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": "attachment;filename=operaciones.xlsx"})

    # Exportación PDF
    if formato == "pdf":
        output = BytesIO()
        pdf = canvas.Canvas(output, pagesize=letter)
        pdf.setTitle("Reporte de Operaciones")
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, 750, "Reporte de Operaciones")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, 730, f"Estado: {
                       estado_filtro.capitalize() if estado_filtro != 'all' else 'Todos'}")
        pdf.drawString(50, 715, f"Fecha: {
                       fecha_filtro if fecha_filtro else 'Todas las fechas'}")
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, 690, "ID")
        pdf.drawString(100, 690, "Descripción")
        pdf.drawString(300, 690, "Estado")
        pdf.drawString(400, 690, "Fecha")
        y = 675
        pdf.setFont("Helvetica", 10)
        for operacion in operaciones:
            pdf.drawString(50, y, str(operacion["id_operacion"] or ""))
            pdf.drawString(100, y, str(operacion["descripcion"] or "")[:40])
            pdf.drawString(300, y, str(operacion["estado"] or ""))
            pdf.drawString(400, y, str(operacion["fecha"] or ""))
            y -= 15
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = 750
        pdf.save()
        output.seek(0)
        return Response(output, mimetype="application/pdf",
                        headers={"Content-Disposition": "attachment;filename=operaciones.pdf"})

    return "Formato no soportado", 400


@app.route("/operaciones/delete/<int:id>", methods=["POST"])
def eliminar_operacion(id):
    if 'user_id' not in session:
        return redirect("/")

    try:
        conn = sqlite3.connect("plataforma.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Verificar si la operación es eliminable
        cursor.execute(
            "SELECT * FROM operaciones WHERE id_operacion = ?", (id,))
        operacion = cursor.fetchone()

        if not operacion:
            return redirect("/operaciones?error=OperacionNoEncontrada")

        # Validar el estado de la operación
        if operacion["estado"] == "completado":
            return redirect("/operaciones?error=OperacionCritica")

        # Si pasa las validaciones, eliminar la operación
        cursor.execute("DELETE FROM operaciones WHERE id_operacion = ?", (id,))
        conn.commit()
        conn.close()
        return redirect("/operaciones?success=OperacionEliminada")
    except sqlite3.Error as e:
        print(f"Error al eliminar la operación: {e}")
        return redirect("/operaciones?error=ErrorDesconocido")


@app.route("/operaciones/ver/<int:id>")
def ver_operacion(id):
    if 'user_id' not in session:
        return redirect("/")

    try:
        conn = sqlite3.connect("plataforma.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Obtener los detalles de la operación
        cursor.execute(
            "SELECT * FROM operaciones WHERE id_operacion = ?", (id,))
        operacion = cursor.fetchone()

        if not operacion:
            return redirect("/operaciones?error=OperacionNoEncontrada")

        conn.close()
        return render_template("operaciones/ver.html", operacion=operacion)

    except sqlite3.Error as e:
        print(f"Error al obtener los detalles de la operación: {e}")
        return redirect("/operaciones?error=ErrorDesconocido")


@app.route("/operaciones/create")
def operaciones_create():
    conn = sqlite3.connect("plataforma.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nombre_completo FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template("operaciones/create.html", usuarios=usuarios)


@app.route("/operaciones/save", methods=["POST"])
def operaciones_save():
    descripcion = request.form['descripcion']
    id_usuario = request.form['id_usuario']

    conn = sqlite3.connect("plataforma.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO operaciones (descripcion, id_usuario) VALUES (?, ?)",
                   (descripcion, id_usuario))
    conn.commit()
    conn.close()
    return redirect("/operaciones")


@app.route("/operaciones/cambiar_estado/<int:id>", methods=["POST"])
def operaciones_cambiar_estado(id):
    if 'user_id' not in session:
        return redirect("/")

    nuevo_estado = request.form["estado"]
    conn = sqlite3.connect("plataforma.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE operaciones
        SET estado = ?
        WHERE id_operacion = ?
    """, (nuevo_estado, id))
    conn.commit()
    conn.close()
    return redirect("/operaciones")


@app.route("/cotizaciones")
def cotizaciones():
    if 'user_id' not in session:
        return redirect("/")
    conn = sqlite3.connect("plataforma.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM cotizaciones WHERE id_usuario = ?", (session['user_id'],))
    cotizaciones = cursor.fetchall()
    conn.close()
    return render_template("cotizaciones/index.html", cotizaciones=cotizaciones)


@app.route("/cotizaciones/create")
def cotizaciones_create():
    return render_template("cotizaciones/create.html")


@app.route("/cotizaciones/save", methods=["POST"])
def cotizaciones_save():
    producto = request.form["producto"]
    pais_origen = request.form["pais_origen"]
    peso = float(request.form["peso"])
    dimensiones = request.form["dimensiones"]
    valor_declarado = float(request.form["valor_declarado"])
    id_usuario = session["user_id"]

    # Lógica para calcular el costo total
    costo_transporte = peso * 5.0  # Ejemplo: $5 por kg
    impuesto_aduanero = valor_declarado * 0.15  # Ejemplo: 15% del valor declarado
    costo_total = costo_transporte + impuesto_aduanero

    conn = sqlite3.connect("plataforma.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cotizaciones (producto, peso, dimensiones, valor_declarado, pais_origen, costo_total, id_usuario)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (producto, peso, dimensiones, valor_declarado, pais_origen, costo_total, id_usuario))
    conn.commit()
    conn.close()
    return redirect("/cotizaciones")


# @app.route("/cotizaciones/aceptar/<int:id>", methods=["GET", "POST"])
# def cotizaciones_aceptar(id):
#     if 'user_id' not in session:
#         return redirect("/")

#     conn = sqlite3.connect("plataforma.db")
#     cursor = conn.cursor()

#     # Recuperar los datos de la cotización aceptada
#     cursor.execute("SELECT * FROM cotizaciones WHERE id_cotizacion = ?", (id,))
#     cotizacion = cursor.fetchone()

#     if cotizacion:
#         descripcion = f"Operación creada a partir de la cotización {
#             cotizacion[1]}"
#         cursor.execute("""
#             INSERT INTO operaciones (descripcion, estado, id_usuario, id_cotizacion)
#             VALUES (?, 'pendiente', ?, ?)
#         """, (descripcion, session['user_id'], id))
#         conn.commit()

#     conn.close()
#     return redirect("/operaciones")


@app.route("/cotizaciones/aceptar/<int:id>", methods=["POST", "GET"])
def cotizaciones_aceptar(id):
    if 'user_id' not in session:
        return redirect("/")

    conn = sqlite3.connect("plataforma.db")
    cursor = conn.cursor()

    # Recuperar la cotización aceptada
    cursor.execute("SELECT * FROM cotizaciones WHERE id_cotizacion = ?", (id,))
    cotizacion = cursor.fetchone()

    if cotizacion:
        descripcion = f"Operación basada en la cotización #{
            cotizacion[0]} - {cotizacion[1]}"
        fecha_actual = datetime.now().strftime(
            "%Y-%m-%d")  # Formato de fecha: AAAA-MM-DD
        cursor.execute("""
            INSERT INTO operaciones (descripcion, estado, id_usuario, id_cotizacion, fecha)
            VALUES (?, 'pendiente', ?, ?, ?)
        """, (descripcion, session['user_id'], id, fecha_actual))
        conn.commit()

    conn.close()
    return redirect("/operaciones")


@app.route("/cotizaciones/edit/<int:id>")
def cotizaciones_edit(id):
    if 'user_id' not in session:
        return redirect("/")
    conn = sqlite3.connect("plataforma.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cotizaciones WHERE id_cotizacion = ?", (id,))
    cotizacion = cursor.fetchone()
    conn.close()
    if cotizacion:
        return render_template("cotizaciones/edit.html", cotizacion=cotizacion)
    else:
        return redirect("/cotizaciones")


# @app.route("/cotizaciones/update", methods=["POST"])
# def cotizaciones_update():
#     id_cotizacion = request.form["id_cotizacion"]
#     producto = request.form["producto"]
#     pais_origen = request.form["pais_origen"]
#     peso = request.form["peso"]
#     dimensiones = request.form["dimensiones"]
#     valor_declarado = request.form["valor_declarado"]

#     conn = sqlite3.connect("plataforma.db")
#     cursor = conn.cursor()
#     cursor.execute("""
#         UPDATE cotizaciones
#         SET producto = ?, pais_origen = ?, peso = ?, dimensiones = ?, valor_declarado = ?
#         WHERE id_cotizacion = ?
#     """, (producto, pais_origen, peso, dimensiones, valor_declarado, id_cotizacion))
#     conn.commit()
#     conn.close()
#     return redirect("/cotizaciones")

@app.route("/cotizaciones/update", methods=["POST"])
def cotizaciones_update():
    id_cotizacion = request.form["id_cotizacion"]
    producto = request.form["producto"]
    pais_origen = request.form["pais_origen"]
    peso = float(request.form["peso"])
    dimensiones = request.form["dimensiones"]
    valor_declarado = float(request.form["valor_declarado"])

    # Lógica para recalcular el costo total
    costo_transporte = peso * 5.0  # Ejemplo: $5 por kg
    impuesto_aduanero = valor_declarado * 0.15  # Ejemplo: 15% del valor declarado
    costo_total = costo_transporte + impuesto_aduanero

    # Actualizar la cotización en la base de datos
    try:
        conn = sqlite3.connect("plataforma.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE cotizaciones
            SET producto = ?, pais_origen = ?, peso = ?, dimensiones = ?, valor_declarado = ?, costo_total = ?
            WHERE id_cotizacion = ?
        """, (producto, pais_origen, peso, dimensiones, valor_declarado, costo_total, id_cotizacion))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al actualizar la cotización: {e}")
        return redirect("/cotizaciones")
    finally:
        conn.close()

    # Redirigir a la lista de cotizaciones con un mensaje de éxito
    return redirect(url_for("cotizaciones", success="Cotización actualizada correctamente"))


@app.route("/cotizaciones/delete/<int:id>", methods=["POST", "GET"])
def cotizaciones_delete(id):
    if 'user_id' not in session:
        return redirect("/")
    try:
        conn = sqlite3.connect("plataforma.db")
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM cotizaciones WHERE id_cotizacion = ?", (id,))
        conn.commit()
        conn.close()
        return redirect("/cotizaciones")
    except sqlite3.Error as e:
        print(f"Error al eliminar la cotización: {e}")
        return redirect("/cotizaciones")


@app.route("/documentos")
def documentos_generales():
    if 'user_id' not in session:
        return redirect("/")
    try:
        conn = sqlite3.connect("plataforma.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Listar todas las operaciones
        cursor.execute("""
        SELECT operaciones.id_operacion, operaciones.descripcion, COUNT(documentos.id_documento) AS total_documentos
        FROM operaciones
        LEFT JOIN documentos ON operaciones.id_operacion = documentos.id_operacion
        WHERE operaciones.id_usuario = ?
        GROUP BY operaciones.id_operacion
        """, (session["user_id"],))
        operaciones = cursor.fetchall()

        conn.close()
        return render_template("documentos/index.html", operaciones=operaciones)
    except sqlite3.Error as e:
        print(f"Error al listar documentos generales: {e}")
        return redirect("/dashboard?error=ErrorAlListarDocumentos")


@app.route("/documentos/<int:operacion_id>")
def ver_documentos(operacion_id):
    if 'user_id' not in session:  # Verifica que el usuario esté autenticado
        return redirect("/")

    try:
        conn = sqlite3.connect("plataforma.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Recuperar detalles de la operación
        cursor.execute(
            "SELECT * FROM operaciones WHERE id_operacion = ?", (operacion_id,))
        operacion = cursor.fetchone()

        # Recuperar documentos asociados a la operación
        cursor.execute("""
        SELECT * FROM documentos
        WHERE id_operacion = ?
        """, (operacion_id,))
        documentos = cursor.fetchall()

        conn.close()

        if not operacion:
            return redirect("/documentos?error=OperacionNoEncontrada")

        return render_template("documentos/ver.html", operacion=operacion, documentos=documentos)
    except sqlite3.Error as e:
        print(f"Error al recuperar documentos: {e}")
        return redirect("/documentos?error=ErrorAlRecuperarDocumentos")


# Ruta para descargar documentos


@app.route("/documentos/descargar/<int:documento_id>")
def descargar_documento(documento_id):
    if 'user_id' not in session:
        return redirect("/")

    try:
        conn = sqlite3.connect("plataforma.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Recuperar información del documento
        cursor.execute(
            "SELECT nombre_archivo, url_archivo FROM documentos WHERE id_documento = ?", (documento_id,))
        documento = cursor.fetchone()

        if not documento:
            return redirect("/documentos?error=DocumentoNoEncontrado")

        # Ruta del archivo en el servidor
        archivo_path = documento["url_archivo"]
        archivo_nombre = documento["nombre_archivo"]

        # Verificar que el archivo existe
        if not os.path.exists(archivo_path):
            return redirect("/documentos?error=ArchivoNoExiste")

        # Servir el archivo
        directorio, archivo = os.path.split(archivo_path)
        return send_from_directory(directorio, archivo, as_attachment=True, download_name=archivo_nombre)
    except sqlite3.Error as e:
        print(f"Error al descargar documento: {e}")
        return redirect("/documentos?error=ErrorAlDescargarDocumento")


UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/documentos/subir/<int:operacion_id>", methods=["POST"])
def subir_documento(operacion_id):
    if 'user_id' not in session:
        return redirect("/")

    if "archivo" not in request.files:
        return redirect(f"/documentos/{operacion_id}?error=ArchivoNoSubido")

    archivo = request.files["archivo"]
    if archivo.filename == "":
        return redirect(f"/documentos/{operacion_id}?error=NombreArchivoInvalido")

    if archivo and allowed_file(archivo.filename):
        filename = secure_filename(archivo.filename)
        ruta = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        archivo.save(ruta)

        try:
            conn = sqlite3.connect("plataforma.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documentos (nombre_archivo, url_archivo, id_operacion)
                VALUES (?, ?, ?)
            """, (filename, ruta, operacion_id))
            conn.commit()
            conn.close()
            return redirect(f"/documentos/{operacion_id}?success=ArchivoSubido")
        except sqlite3.Error as e:
            print(f"Error al subir documento: {e}")
            return redirect(f"/documentos/{operacion_id}?error=ErrorAlSubirDocumento")

    return redirect(f"/documentos/{operacion_id}?error=ArchivoNoPermitido")


@app.route("/documentos/eliminar/<int:documento_id>/<int:operacion_id>", methods=["POST"])
def eliminar_documento(documento_id, operacion_id):
    if 'user_id' not in session:
        return redirect("/")

    try:
        conn = sqlite3.connect("plataforma.db")
        cursor = conn.cursor()

        # Recuperar la ruta del archivo
        cursor.execute(
            "SELECT url_archivo FROM documentos WHERE id_documento = ?", (documento_id,))
        documento = cursor.fetchone()

        if not documento:
            return redirect(f"/documentos/{operacion_id}?error=DocumentoNoEncontrado")

        archivo_path = documento[0]

        # Eliminar el archivo del sistema de archivos si existe
        if os.path.exists(archivo_path):
            os.remove(archivo_path)

        # Eliminar el registro de la base de datos
        cursor.execute(
            "DELETE FROM documentos WHERE id_documento = ?", (documento_id,))
        conn.commit()

        conn.close()
        return redirect(f"/documentos/{operacion_id}?mensaje=DocumentoEliminado")
    except sqlite3.Error as e:
        print(f"Error al eliminar documento: {e}")
        return redirect(f"/documentos/{operacion_id}?error=ErrorAlEliminarDocumento")


@app.route("/documentos/exportar")
def exportar_documentos():
    if 'user_id' not in session:
        return redirect("/")

    formato = request.args.get("formato", "csv").lower()

    if formato not in ["csv", "xlsx", "pdf"]:
        return "Formato no soportado", 400

    try:
        # Conexión y consulta de datos
        conn = sqlite3.connect("plataforma.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        SELECT documentos.id_documento, documentos.nombre_archivo, documentos.url_archivo, operaciones.descripcion AS operacion
        FROM documentos
        LEFT JOIN operaciones ON documentos.id_operacion = operaciones.id_operacion
        """)
        documentos = cursor.fetchall()
        conn.close()

        # Convertir resultados a DataFrame
        data = [{
            "ID Documento": doc["id_documento"],
            "Nombre del Documento": doc["nombre_archivo"],
            "Ruta del Archivo": doc["url_archivo"],
            "Operación Asociada": doc["operacion"]
        } for doc in documentos]

        if formato == "pdf":
            # Exportar a PDF con orientación vertical (portrait)
            output = BytesIO()
            pdf = SimpleDocTemplate(output, pagesize=portrait(letter))
            pdf_data = [["ID Documento", "Nombre del Documento",
                         "Ruta del Archivo", "Operación Asociada"]]  # Header

            # Añadir filas al PDF
            for doc in data:
                pdf_data.append([
                    doc["ID Documento"],
                    doc["Nombre del Documento"],
                    doc["Ruta del Archivo"],
                    doc["Operación Asociada"]
                ])

            # Crear tabla
            table = Table(pdf_data)
            style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ])
            table.setStyle(style)

            elements = [table]
            pdf.build(elements)

            output.seek(0)
            return Response(output, mimetype="application/pdf",
                            headers={"Content-Disposition": "attachment;filename=documentos.pdf"})

        # Exportar CSV y Excel (ya implementado previamente)
        if formato == "csv":
            # Exportar a CSV
            output = BytesIO()
            pd.DataFrame(data).to_csv(output, index=False)
            output.seek(0)
            return Response(output, mimetype="text/csv",
                            headers={"Content-Disposition": "attachment;filename=documentos.csv"})

        elif formato == "xlsx":
            # Exportar a Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                pd.DataFrame(data).to_excel(
                    writer, index=False, sheet_name="Documentos")
            output.seek(0)
            return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment;filename=documentos.xlsx"})

    except Exception as e:
        print(f"Error al exportar documentos: {e}")
        return redirect("/documentos?error=ErrorAlExportar")


# @app.route("/reportes", methods=["GET"])
# def reportes():
#     if 'user_id' not in session:
#         return redirect("/")

#     # Capturar filtros del formulario
#     tipo_reporte = request.args.get("report-type", "operations")
#     fecha_inicio = request.args.get("start-date", "")
#     fecha_fin = request.args.get("end-date", "")

#     # Puedes implementar lógica para procesar estos filtros y generar datos dinámicos
#     return render_template("reportes/index.html", tipo_reporte=tipo_reporte, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)


@app.route("/reportes", methods=["GET"])
def reportes():
    tipo_reporte = request.args.get("tipo", "operaciones").lower()
    fecha_inicio = request.args.get("fecha_inicio", "")
    fecha_fin = request.args.get("fecha_fin", "")

    # Consulta base de datos aquí para generar el reporte
    conn = sqlite3.connect("plataforma.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = ""
    params = []
    if tipo_reporte == "operaciones":
        query = "SELECT id_operacion, descripcion, estado, fecha FROM operaciones WHERE 1=1"
    elif tipo_reporte == "cotizaciones":
        query = "SELECT id_cotizacion, producto, costo_total, valor_declarado FROM cotizaciones WHERE 1=1"
    elif tipo_reporte == "documentos":
        query = """
        SELECT documentos.id_documento, documentos.nombre_archivo, operaciones.descripcion AS operacion
        FROM documentos
        LEFT JOIN operaciones ON documentos.id_operacion = operaciones.id_operacion
        WHERE 1=1
        """

    if fecha_inicio:
        query += " AND fecha >= ?"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND fecha <= ?"
        params.append(fecha_fin)

    cursor.execute(query, params)
    reporte = cursor.fetchall()
    conn.close()

    return render_template("reportes/index.html", reporte=reporte, tipo_reporte=tipo_reporte, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)


@app.route("/reportes/exportar", methods=["GET"])
def exportar_reportes():
    formato = request.args.get("formato", "pdf").lower()
    # Aquí iría la lógica para generar el archivo PDF o Excel
    if formato == "pdf":
        return "Función para exportar PDF no implementada aún"
    elif formato == "excel":
        return "Función para exportar Excel no implementada aún"
    else:
        return "Formato no soportado", 400


@app.route("/reportes", methods=["GET"])
# cambios
def reportees():
    if 'user_id' not in session:
        return redirect("/")

    tipo_reporte = request.args.get("tipo", "operaciones").lower()
    fecha_inicio = request.args.get("fecha_inicio", "")
    fecha_fin = request.args.get("fecha_fin", "")

    conn = sqlite3.connect("plataforma.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        if tipo_reporte == "operaciones":
            query = "SELECT id_operacion, descripcion, estado, fecha FROM operaciones WHERE id_usuario = ?"
            params = [session["user_id"]]
        elif tipo_reporte == "cotizaciones":
            query = "SELECT id_cotizacion, producto, costo_total, valor_declarado FROM cotizaciones WHERE id_usuario = ?"
            params = [session["user_id"]]
        elif tipo_reporte == "documentos":
            query = """
                SELECT documentos.id_documento, documentos.nombre_archivo, operaciones.descripcion AS operacion
                FROM documentos
                LEFT JOIN operaciones ON documentos.id_operacion = operaciones.id_operacion
                WHERE operaciones.id_usuario = ?
            """
            params = [session["user_id"]]
        else:
            print("Tipo de reporte inválido")
            return redirect("/reportes?error=TipoReporteInvalido")

        # Filtrar por fecha
        if fecha_inicio:
            query += " AND fecha >= ?"
            params.append(fecha_inicio)
        if fecha_fin:
            query += " AND fecha <= ?"
            params.append(fecha_fin)

        print("Consulta ejecutada:", query)  # Depuración
        print("Parámetros:", params)  # Depuración

        cursor.execute(query, params)
        reporte = cursor.fetchall()

        conn.close()
        return render_template("reportes/index.html", reporte=reporte, tipo_reporte=tipo_reporte)
    except Exception as e:
        # Imprime el error en la consola
        print(f"Error al generar reporte: {e}")
        conn.close()
        return redirect("/reportes?error=ErrorGenerandoReporte")


if __name__ == "__main__":
    app.run(debug=True)
