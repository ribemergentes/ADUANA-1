import sqlite3


def agregar_datos(tabla, datos):
    """
    Inserta datos en una tabla de SQLite.

    :param tabla: Nombre de la tabla donde se insertarán los datos.
    :param datos: Diccionario con los nombres de las columnas como claves y los valores a insertar.
    """
    try:
        # Conexión a la base de datos
        conn = sqlite3.connect("plataforma.db")
        cursor = conn.cursor()

        # Construcción de la consulta SQL
        # Ejemplo: "nombre_completo, correo, contrasena"
        columnas = ", ".join(datos.keys())
        # Ejemplo: "?, ?, ?"
        marcadores = ", ".join(["?" for _ in datos.values()])
        sql = f"INSERT INTO {tabla} ({columnas}) VALUES ({marcadores})"

        # Ejecución de la consulta
        cursor.execute(sql, tuple(datos.values()))
        conn.commit()
        print(f"Datos insertados en la tabla '{tabla}' correctamente.")
    except sqlite3.Error as e:
        print(f"Error al insertar datos en '{tabla}': {e}")
    finally:
        conn.close()

# Ejemplo de uso: Insertar datos en diferentes tablas


if __name__ == "__main__":
    # Insertar en la tabla 'usuarios'
    datos_usuario = {
        "nombre_completo": "ronaldo",
        "correo": "ronaldo@admin.com",
        "contrasena": "admin"
    }
    agregar_datos("usuarios", datos_usuario)

    # Insertar en la tabla 'operaciones'
    datos_operacion = {
        "descripcion": "Importación de textiles",
        "estado": "pendiente",
        "id_usuario": 1  # Asegúrate de que el ID de usuario exista
    }
    agregar_datos("operaciones", datos_operacion)

    # Insertar en la tabla 'cotizaciones'
    datos_cotizacion = {
        "producto": "Maquinaria",
        "peso": 1500.50,
        "dimensiones": "120x80x100",
        "valor_declarado": 25000.00,
        "id_usuario": 1  # Asegúrate de que el ID de usuario exista
    }
    agregar_datos("cotizaciones", datos_cotizacion)
