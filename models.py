from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Usuario(db.Model):
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(255), nullable=False)


class Operacion(db.Model):
    id_operacion = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(50), default='pendiente')
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))

# Más modelos como Cotizacion, Documento y Notificacion se agregarían aquí
