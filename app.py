from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import random
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
import os
from functools import wraps
import hashlib
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Para usar matplotlib en modo no interactivo
import numpy as np
from datetime import datetime, timedelta
from flask import send_from_directory
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import string

# Definir la ruta de la carpeta para los gráficos
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
IMAGES_FOLDER = os.path.join(STATIC_FOLDER, 'images')
os.makedirs(IMAGES_FOLDER, exist_ok=True)

app = Flask(__name__)
# Usar variables de entorno para configuraciones sensibles
app.secret_key = os.environ.get('SECRET_KEY', 'tu_clave_secreta_temporal')

# Configuración de MySQL
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'Ericko11$')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'encuestas_db')

# Configuración de email
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'takenokamu@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'kcdvjijtgcsucvmb')

mysql = MySQL(app)

# ----- Funciones auxiliares -----

# Agregar esta función para generar códigos de cupón aleatorios alfanuméricos
def generar_codigo_cupon():
    """Genera un código alfanumérico aleatorio de 6 caracteres para cupones"""
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(caracteres) for _ in range(6))

# Agregar función para enviar cupón por correo
def enviar_cupon(destinatario, codigo, porcentaje):
    """Envía un correo con el cupón de descuento correspondiente"""
    try:
        # Crear un mensaje multipart
        mensaje = MIMEMultipart()
        mensaje['Subject'] = f'Tu cupón de {porcentaje}% de descuento - Gracias por tu encuesta'
        mensaje['From'] = EMAIL_SENDER
        mensaje['To'] = destinatario
        
        # Texto del correo
        texto = f'''
        Hola,
        
        ¡Gracias por responder nuestra encuesta de satisfacción!
        
        Como agradecimiento, te enviamos un cupón de {porcentaje}% de descuento para tu próxima visita.
        
        Tu código de cupón es: {codigo}
        
        Este cupón es válido por 30 días a partir de hoy.
        
        ¡Esperamos verte pronto!
        
        Saludos,
        El equipo de Encuestas
        '''
        
        # Agregar parte de texto al mensaje
        parte_texto = MIMEText(texto)
        mensaje.attach(parte_texto)
        
        # Agregar imagen del cupón
        ruta_imagen = os.path.join(STATIC_FOLDER, 'images', f'cupon_{porcentaje}.png')
        if os.path.exists(ruta_imagen):
            with open(ruta_imagen, 'rb') as img:
                imagen = MIMEImage(img.read())
                imagen.add_header('Content-ID', '<cupon>')
                imagen.add_header('Content-Disposition', 'inline', filename=f'cupon_{porcentaje}.png')
                mensaje.attach(imagen)

        # Enviar correo
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(mensaje)
        return True
    except Exception as e:
        print(f"Error al enviar email con cupón: {e}")
        return False


def hash_password(password):
    """Función para hashear contraseñas de forma segura"""
    return hashlib.sha256(password.encode()).hexdigest()

def generar_codigo_verificacion():
    """Genera un código de verificación de 6 dígitos"""
    return str(random.randint(100000, 999999))

def enviar_codigo_verificacion(destinatario, codigo):
    """Envía un correo con el código de verificación"""
    try:
        mensaje = EmailMessage()
        mensaje['Subject'] = 'Tu código de verificación - Encuesta de Satisfacción'
        mensaje['From'] = EMAIL_SENDER
        mensaje['To'] = destinatario
        mensaje.set_content(f'''
        Hola,
        
        Gracias por registrarte en nuestro sistema de encuestas de satisfacción.
        
        Tu código de verificación es: {codigo}
        
        Si no solicitaste este código, puedes ignorar este correo.
        
        Saludos,
        El equipo de Encuestas
        ''')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(mensaje)
        return True
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return False

def login_required(f):
    """Decorador para proteger rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Debes iniciar sesión para acceder a esta página", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Modifica la función verificar_actividad_reciente para incluir verificación de cupon
def verificar_actividad_reciente(id_usuario):
    """Verifica si el usuario ha respondido la encuesta en los últimos 30 días"""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT fecha_respuesta FROM respuestas
        WHERE id_usuario = %s
        ORDER BY fecha_respuesta DESC
        LIMIT 1
    """, (id_usuario,))
    ultima_respuesta = cur.fetchone()
    
    if ultima_respuesta:
        fecha_ultima = ultima_respuesta[0]
        hace_un_mes = datetime.now() - timedelta(days=30)
        if fecha_ultima > hace_un_mes:
            return True
    
    return False

def enviar_codigo_recuperacion(destinatario, codigo):
    """Envía un correo con el código de recuperación de contraseña"""
    try:
        mensaje = EmailMessage()
        mensaje['Subject'] = 'Recuperación de Contraseña - Encuesta de Satisfacción'
        mensaje['From'] = EMAIL_SENDER
        mensaje['To'] = destinatario
        mensaje.set_content(f'''
        Hola,
        
        Has solicitado recuperar tu contraseña en nuestro sistema de encuestas de satisfacción.
        
        Tu código de verificación es: {codigo}
        
        Este código expirará en 30 minutos.
        
        Si no solicitaste este código, puedes ignorar este correo.
        
        Saludos,
        El equipo de Encuestas
        ''')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(mensaje)
        return True
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return False

    return False

# --- Funciones auxiliares para gráficos ---
def generar_grafico_barras(datos, etiquetas, titulo, etiqueta_x, etiqueta_y, nombre_archivo, promedio=None):
    """
    Genera un gráfico de barras
    
    Args:
        datos: Lista de valores numéricos para las barras
        etiquetas: Lista de etiquetas para las barras
        titulo: Título del gráfico
        etiqueta_x: Etiqueta del eje X
        etiqueta_y: Etiqueta del eje Y
        nombre_archivo: Nombre del archivo a guardar (sin extensión)
        promedio: Valor del promedio para dibujar una línea horizontal (opcional)
    """
    plt.figure(figsize=(12, 6))
    plt.bar(etiquetas, datos, color='#335435', alpha=0.8)
    
    if promedio is not None:
        plt.axhline(y=promedio, color='r', linestyle='--', 
                    label=f'Promedio: {promedio}')
        plt.legend()
    
    plt.ylim(0, max(datos) * 1.1 if datos else 5.5)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel(etiqueta_y)
    plt.xlabel(etiqueta_x)
    plt.title(titulo)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_FOLDER, f'{nombre_archivo}.png'))
    plt.close()

def generar_grafico_pastel(datos, etiquetas, titulo, nombre_archivo, colores=None):
    """
    Genera un gráfico de pastel
    
    Args:
        datos: Lista de valores numéricos para las porciones
        etiquetas: Lista de etiquetas para las porciones
        titulo: Título del gráfico
        nombre_archivo: Nombre del archivo a guardar (sin extensión)
        colores: Lista de colores para las porciones (opcional)
    """
    if not colores:
        colores = ['#4CAF50', '#F44336', '#2196F3', '#FFC107', '#9C27B0', '#FF5722']
    
    plt.figure(figsize=(8, 8))
    plt.pie(datos, labels=etiquetas, colors=colores, autopct='%1.1f%%', 
            startangle=90, shadow=True)
    plt.axis('equal')
    plt.title(titulo)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_FOLDER, f'{nombre_archivo}.png'))
    plt.close()

def generar_grafico_histograma(datos, bins, etiquetas_bins, titulo, etiqueta_x, etiqueta_y, nombre_archivo):
    """
    Genera un histograma
    
    Args:
        datos: Serie de pandas con los datos
        bins: Lista con los límites de los bins
        etiquetas_bins: Lista con las etiquetas de los ejes X
        titulo: Título del gráfico
        etiqueta_x: Etiqueta del eje X
        etiqueta_y: Etiqueta del eje Y
        nombre_archivo: Nombre del archivo a guardar (sin extensión)
    """
    plt.figure(figsize=(10, 6))
    plt.hist(datos, bins=bins, rwidth=0.8, color='#335435', alpha=0.8)
    plt.xticks(etiquetas_bins)
    plt.xlabel(etiqueta_x)
    plt.ylabel(etiqueta_y)
    plt.title(titulo)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_FOLDER, f'{nombre_archivo}.png'))
    plt.close()

# ----- Rutas -----

@app.route('/')
def index():
    """Ruta principal que redirecciona al login"""
    return redirect(url_for('login'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Ruta para el registro de usuarios"""
    error = None
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        correo = request.form.get('correo', '').strip()
        telefono = request.form.get('telefono', '').strip()
        contrasena = request.form.get('contrasena', '')
        
        # Validaciones básicas
        if not all([nombre, apellido, correo, telefono, contrasena]):
            error = "Todos los campos son obligatorios"
            return render_template('registro.html', error=error)
            
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        
        if cur.fetchone():
            error = "El correo ya está registrado"
        else:
            codigo = generar_codigo_verificacion()
            # Almacenar contraseña hasheada
            contrasena_hash = hash_password(contrasena)
            
            cur.execute("""
                INSERT INTO usuarios (privilegios, nombre, apellido, correo, telefono, contraseña, codigo_verificacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (0, nombre, apellido, correo, telefono, contrasena_hash, codigo))
            mysql.connection.commit()
            cur.close()

            if enviar_codigo_verificacion(correo, codigo):
                session['correo_verificacion'] = correo
                return redirect(url_for('verificar_codigo'))
            else:
                error = "Error al enviar el código de verificación. Intenta de nuevo."
        
        cur.close()

    return render_template('registro.html', error=error)

@app.route('/verificar_codigo', methods=['GET', 'POST'])
def verificar_codigo():
    """Ruta para verificar el código enviado por correo"""
    mensaje = None
    verificado = False
    
    if 'correo_verificacion' not in session:
        return redirect(url_for('registro'))
    
    correo = session.get('correo_verificacion')
    
    # Verificar si necesitamos reenviar un código (cuando llegamos desde login)
    reenviar = request.args.get('reenviar', 'false') == 'true'
    if request.method == 'GET' and reenviar:
        codigo = generar_codigo_verificacion()
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE usuarios 
            SET codigo_verificacion = %s 
            WHERE correo = %s
        """, (codigo, correo))
        mysql.connection.commit()
        cur.close()
        
        if enviar_codigo_verificacion(correo, codigo):
            mensaje = "Se ha enviado un nuevo código de verificación a tu correo."
        else:
            mensaje = "Error al enviar el código de verificación. Intenta nuevamente."
    
    if request.method == 'POST':
        codigo_usuario = request.form.get('codigo', '').strip()

        if not codigo_usuario:
            mensaje = "Por favor, ingresa el código de verificación"
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT codigo_verificacion FROM usuarios WHERE correo = %s", (correo,))
            resultado = cur.fetchone()
            
            if resultado and resultado[0] == codigo_usuario:
                cur.execute("""
                UPDATE usuarios 
                SET codigo_verificacion = NULL, verificado = TRUE 
                WHERE correo = %s
                """, (correo,))
                mysql.connection.commit()
                mensaje = "¡Cuenta verificada exitosamente!"
                verificado = True
                session.pop('correo_verificacion', None)
                flash("Tu cuenta ha sido verificada. Ahora puedes iniciar sesión.", "success")
                return redirect(url_for('login'))
            else:
                mensaje = "Código incorrecto. Intenta nuevamente."
            
            cur.close()

    # Agregamos un botón en la plantilla para reenviar el código
    return render_template('verificar_codigo.html', mensaje=mensaje, verificado=verificado, correo=correo)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta para el inicio de sesión"""
    error = None
    usuario = None

    if request.method == 'POST':
        correo = request.form.get('email', '').strip()
        contrasena = request.form.get('password', '')

        if not correo or not contrasena:
            error = "Por favor, completa todos los campos."
            return render_template('login.html', error=error)

        # Hashear la contraseña para comparar
        contrasena_hash = hash_password(contrasena)
        
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id_usuario, nombre, verificado, privilegios, codigo_verificacion
            FROM usuarios 
            WHERE correo = %s
        """, (correo,))
        usuario = cur.fetchone()
        cur.close()

        # Verificamos si el usuario existe
        if usuario:
            # Primero verificamos si el usuario no está verificado pero tiene un código
            if usuario[2] == 0 and usuario[4]:  # verificado=0 y tiene código de verificación
                session['correo_verificacion'] = correo
                flash("Tu cuenta aún no ha sido verificada. Te hemos redirigido a la página de verificación.", "warning")
                return redirect(url_for('verificar_codigo'))
            
            # Ahora verificamos la contraseña
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT id_usuario, nombre, verificado, privilegios
                FROM usuarios 
                WHERE correo = %s AND contraseña = %s
            """, (correo, contrasena_hash))
            usuario_con_clave = cur.fetchone()
            cur.close()
            
            if usuario_con_clave:
                if usuario_con_clave[2] == 1:  # verificado
                    # Reiniciar contador de intentos fallidos si existe
                    if 'intentos_fallidos' in session:
                        session.pop('intentos_fallidos')
                    if 'email_intentos' in session:
                        session.pop('email_intentos')
                        
                    session['usuario_id'] = usuario_con_clave[0]
                    session['nombre'] = usuario_con_clave[1]
                    session['privilegios'] = usuario_con_clave[3]
                    
                    print(f"Usuario autenticado - ID: {usuario_con_clave[0]}, Nombre: {usuario_con_clave[1]}, Privilegios: {usuario_con_clave[3]}")
                    
                    # Redireccionar según privilegios
                    if usuario_con_clave[3] == 1:  # Específicamente si es administrador (privilegio = 1)
                        print("Redirigiendo a admin_reportes_sucursal")
                        return redirect(url_for('admin_reportes_sucursal'))
                    else:  # Usuario normal
                        print("Redirigiendo a encuesta")
                        return redirect(url_for('encuesta'))
                else:
                    # Usuario no verificado, lo redirigimos a la verificación
                    session['correo_verificacion'] = correo
                    flash("Tu cuenta aún no ha sido verificada. Por favor completa la verificación.", "warning")
                    return redirect(url_for('verificar_codigo'))
            else:
                # Contraseña incorrecta
                # Incrementar contador de intentos fallidos
                if 'intentos_fallidos' not in session or 'email_intentos' not in session or session['email_intentos'] != correo:
                    session['intentos_fallidos'] = 1
                    session['email_intentos'] = correo
                else:
                    session['intentos_fallidos'] += 1
                
                # Verificar si se han superado los intentos máximos
                if session.get('intentos_fallidos', 0) >= 3:
                    session['correo_recuperacion'] = correo
                    # Reiniciar contador
                    session.pop('intentos_fallidos', None)
                    session.pop('email_intentos', None)
                    return redirect(url_for('recuperar_contrasena'))
                
                intentos_restantes = 3 - session.get('intentos_fallidos', 0)
                error = f"Contraseña incorrecta. Te quedan {intentos_restantes} intentos."
        else:
            error = "No existe una cuenta con ese correo electrónico."

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario"""
    session.clear()
    flash("Has cerrado sesión correctamente", "success")
    return redirect(url_for('login'))

# Modifica la ruta /encuesta para que se genere y envíe el cupón
@app.route('/encuesta', methods=['GET', 'POST'])
@login_required
def encuesta():
    """Ruta para responder la encuesta"""
    id_usuario = session['usuario_id']

    # Verificar si el usuario ya respondió en los últimos 30 días
    if verificar_actividad_reciente(id_usuario):
        flash("Ya has respondido la encuesta este mes. ¡Gracias!", "warning")
        return redirect(url_for('agradecimiento'))

    # Procesar envío del formulario
    if request.method == 'POST':
        try:
            # Obtener datos del formulario con validación
            pais = request.form.get('pais', '').strip()
            sucursal = request.form.get('sucursal', '').strip()
            calidad_comida = int(request.form.get('calidad_comida', 0))
            tiempo_espera = request.form.get('tiempo_espera', '').strip()
            atencion_personal = int(request.form.get('atencion_personal', 0))
            agrado_sucursal = request.form.get('agrado_sucursal', '').strip()
            volveria_visitar = request.form.get('volveria_visitar', '').strip()
            area_mejora = request.form.get('area_mejora', '').strip()
            calificacion_general = int(request.form.get('calificacion_general', 0))

            # Validación básica
            if not all([pais, sucursal, tiempo_espera, agrado_sucursal, volveria_visitar]):
                flash("Por favor, complete todos los campos requeridos", "danger")
                return redirect(url_for('encuesta'))

            # Guardar respuesta en la base de datos
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO respuestas (
                    id_usuario, pais, sucursal, calidad_comida, tiempo_espera,
                    atencion_personal, agrado_sucursal, volveria_visitar,
                    area_mejora, calificacion_general, fecha_respuesta
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                id_usuario, pais, sucursal, calidad_comida, tiempo_espera,
                atencion_personal, agrado_sucursal, volveria_visitar,
                area_mejora, calificacion_general
            ))
            mysql.connection.commit()
            
            # Generar cupón aleatorio (30%, 35% o 40%)
            porcentajes = [30, 35, 40]
            porcentaje_elegido = random.choice(porcentajes)
            
            # Generar código de cupón único
            while True:
                codigo_cupon = generar_codigo_cupon()
                # Verificar que el código no exista ya
                cur.execute("SELECT id_cupon FROM cupones WHERE codigo = %s", (codigo_cupon,))
                if not cur.fetchone():
                    break
            
            # Calcular fecha de vencimiento (30 días desde hoy)
            fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Guardar cupón en la base de datos
            cur.execute("""
                INSERT INTO cupones (
                    id_usuario, codigo, porcentaje, fecha_vencimiento
                ) VALUES (%s, %s, %s, %s)
            """, (
                id_usuario, codigo_cupon, porcentaje_elegido, fecha_vencimiento
            ))
            mysql.connection.commit()
            
            # Obtener email del usuario
            cur.execute("SELECT correo FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            correo_usuario = cur.fetchone()[0]
            
            cur.close()
            
            # Enviar cupón por correo
            enviar_cupon(correo_usuario, codigo_cupon, porcentaje_elegido)

            flash("¡Gracias por tu respuesta! Te hemos enviado un cupón de descuento.", "success")
            return redirect(url_for('agradecimiento'))

        except Exception as e:
            print(f"Error al guardar la respuesta: {e}")
            flash("Ocurrió un error. Intenta nuevamente.", "danger")
            return redirect(url_for('encuesta'))

    return render_template('encuesta.html', nombre=session.get('nombre', ''))


@app.route('/agradecimiento')
@login_required
def agradecimiento():
    """Página de agradecimiento después de completar la encuesta"""
    return render_template('agradecimiento.html')

@app.route('/admin/reportes_sucursal')
@login_required
def admin_reportes_sucursal():
    """Página para visualizar reportes por sucursal"""
    # Verificar si el usuario es administrador
    if session.get('privilegios', 0) != 1:  # Específicamente verificar si es administrador (privilegio = 1)
        flash("No tienes permiso para acceder a esta página", "danger")
        return redirect(url_for('encuesta'))
    
    # Obtener parámetros de filtro
    pais_seleccionado = request.args.get('pais', '')
    sucursal_seleccionada = request.args.get('sucursal', '')
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    
    # Si no hay fechas seleccionadas, usar último mes
    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_fin:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
    
    # Consultar datos
    cur = mysql.connection.cursor()
    
    # Lista de países disponibles
    cur.execute("SELECT DISTINCT pais FROM respuestas ORDER BY pais")
    paises = [row[0] for row in cur.fetchall()]
    
    # Lista de sucursales (filtradas por país si está seleccionado)
    if pais_seleccionado:
        cur.execute("SELECT DISTINCT sucursal FROM respuestas WHERE pais = %s ORDER BY sucursal", (pais_seleccionado,))
    else:
        cur.execute("SELECT DISTINCT sucursal FROM respuestas ORDER BY sucursal")
    sucursales = [row[0] for row in cur.fetchall()]
    
    # Construir consulta base con filtros para resumen
    query_base = """
        SELECT r.*, u.nombre, u.apellido
        FROM respuestas r
        JOIN usuarios u ON r.id_usuario = u.id_usuario
        WHERE 1=1
    """
    params = []
    
    if pais_seleccionado:
        query_base += " AND r.pais = %s"
        params.append(pais_seleccionado)
    
    if sucursal_seleccionada:
        query_base += " AND r.sucursal = %s"
        params.append(sucursal_seleccionada)
    
    if fecha_inicio:
        query_base += " AND r.fecha_respuesta >= %s"
        params.append(fecha_inicio)
    
    if fecha_fin:
        query_base += " AND r.fecha_respuesta <= %s"
        params.append(fecha_fin + " 23:59:59")
    
    # Obtener datos con filtros
    cur.execute(query_base + " ORDER BY r.fecha_respuesta DESC", tuple(params))
    datos = cur.fetchall()
    
    # Cerrar cursor
    cur.close()
    
    # Procesar datos con pandas
    if datos:
        # Nombres de columnas según tu estructura de tablas
        columnas = ['id_respuesta', 'pais', 'sucursal', 'calidad_comida', 
                    'tiempo_espera', 'atencion_personal', 'agrado_sucursal', 
                    'volveria_visitar', 'area_mejora', 'calificacion_general', 
                    'fecha_respuesta', 'id_usuario', 'nombre', 'apellido']
        
        # Crear DataFrame
        df = pd.DataFrame(datos, columns=columnas)

        # Convertir explícitamente las columnas numéricas
        df['calificacion_general'] = pd.to_numeric(df['calificacion_general'], errors='coerce')
        df['calidad_comida'] = pd.to_numeric(df['calidad_comida'], errors='coerce')
        df['atencion_personal'] = pd.to_numeric(df['atencion_personal'], errors='coerce')

        # Calcular métricas asegurando que los valores son numéricos
        total_respuestas = len(df)

        # Calcular promedios solo con valores válidos
        promedio_calificacion = round(df['calificacion_general'].mean(), 1) if not df['calificacion_general'].isna().all() else 0
        satisfaccion_servicio = round(df['atencion_personal'].mean() * 10, 1) if not df['atencion_personal'].isna().all() else 0

        # Para volveria_visitar, contar las respuestas afirmativas
        tasa_retorno = round((df['volveria_visitar'] == 'si').sum() / df['volveria_visitar'].count() * 100, 1) if df['volveria_visitar'].count() > 0 else 0

        # Procesar datos por sucursal
        datos_sucursales = []

        # Agrupar por sucursal
        sucursales_grupo = df.groupby('sucursal')

        for sucursal, grupo in sucursales_grupo:
            # Calcular indicadores para cada sucursal
            total_sucursal = len(grupo)
            
            # Calidad comida (promedio)
            calidad_promedio = round(grupo['calidad_comida'].mean(), 1) if not grupo['calidad_comida'].isna().all() else 0
            
            # Atención personal (promedio)
            atencion_promedio = round(grupo['atencion_personal'].mean(), 1) if not grupo['atencion_personal'].isna().all() else 0
            
            # Tiempo de espera (porcentaje de respuestas 'si')
            tiempo_adecuado = round((grupo['tiempo_espera'] == 'si').sum() / grupo['tiempo_espera'].count() * 100, 1) if grupo['tiempo_espera'].count() > 0 else 0
            
            # Calificación general (promedio)
            calificacion_promedio = round(grupo['calificacion_general'].mean(), 1) if not grupo['calificacion_general'].isna().all() else 0
            
            # Intención de retorno (porcentaje de respuestas 'si')
            intencion_retorno = round((grupo['volveria_visitar'] == 'si').sum() / grupo['volveria_visitar'].count() * 100, 1) if grupo['volveria_visitar'].count() > 0 else 0
            
            datos_sucursales.append({
                'sucursal': sucursal,
                'total_respuestas': total_sucursal,
                'calidad_comida': calidad_promedio,
                'atencion_personal': atencion_promedio,
                'tiempo_espera': tiempo_adecuado,
                'calificacion_general': calificacion_promedio,
                'intencion_retorno': intencion_retorno
            })

        # Ordenar por calificación general (descendente)
        datos_sucursales = sorted(datos_sucursales, key=lambda x: x['calificacion_general'], reverse=True)

        # 1. Generar gráfico de calificaciones por sucursal
        if total_respuestas > 0:
            plt.figure(figsize=(12, 6))
            
            # Limitamos a las 10 primeras sucursales si hay muchas
            sucursales_plot = datos_sucursales[:10] if len(datos_sucursales) > 10 else datos_sucursales
            
            # Crear listas para el gráfico
            nombres_sucursales = [item['sucursal'] for item in sucursales_plot]
            calificaciones = [item['calificacion_general'] for item in sucursales_plot]
            
            plt.bar(nombres_sucursales, calificaciones, color='#335435', alpha=0.8)
            plt.axhline(y=promedio_calificacion, color='r', linestyle='--', 
                        label=f'Promedio: {promedio_calificacion}')
            plt.ylim(0, 5.5)
            plt.xticks(rotation=45, ha='right')
            plt.ylabel('Calificación Promedio')
            plt.title('Calificación Promedio por Sucursal')
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(IMAGES_FOLDER, 'chart_sucursales.png'))
            plt.close()
            
            # 2. Generar gráfico de distribución de calificaciones
            valid_ratings = df['calificacion_general'].dropna()
            if len(valid_ratings) > 0:
                plt.figure(figsize=(10, 6))
                
                # Crear histograma de calificaciones con valores válidos
                plt.hist(valid_ratings, bins=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5], 
                        rwidth=0.8, color='#335435', alpha=0.8)
                plt.xticks([1, 2, 3, 4, 5])
                plt.xlabel('Calificación')
                plt.ylabel('Número de Respuestas')
                plt.title('Distribución de Calificaciones Generales')
                plt.tight_layout()
                plt.savefig(os.path.join(IMAGES_FOLDER, 'chart_distribucion.png'))
                plt.close()
                
            # 3. Generar gráfico de pastel para intención de retorno
            plt.figure(figsize=(8, 8))
            # Contar valores de volveria_visitar
            volveria_counts = df['volveria_visitar'].value_counts()
            # Asegurar que 'si' y 'no' existan en el conteo
            si_count = volveria_counts.get('si', 0)
            no_count = volveria_counts.get('no', 0)
            counts = [si_count, no_count]
            labels = ['Sí', 'No']
            colors = ['#4CAF50', '#F44336']
            
            plt.pie(counts, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, shadow=True)
            plt.axis('equal')  # Para que el gráfico sea circular
            plt.title('Intención de Retorno')
            plt.tight_layout()
            plt.savefig(os.path.join(IMAGES_FOLDER, 'chart_retorno.png'))
            plt.close()
            
        # Preparar datos para la tabla de respuestas individuales
        # Formatear la columna de fecha para mostrarla mejor
        df['fecha_formateada'] = df['fecha_respuesta'].apply(lambda x: x.strftime('%d/%m/%Y %H:%M') if pd.notnull(x) else '')
        
        # Crear lista de respuestas para mostrar en la tabla
        respuestas_tabla = []
        for _, row in df.iterrows():
            respuestas_tabla.append({
                'nombre': f"{row['nombre']} {row['apellido']}",
                'fecha': row['fecha_formateada'],
                'calidad_comida': row['calidad_comida'],
                'tiempo_espera': 'Sí' if row['tiempo_espera'] == 'si' else 'No',
                'atencion_personal': row['atencion_personal'],
                'agrado_sucursal': 'Sí' if row['agrado_sucursal'] == 'si' else 'No',
                'volveria_visitar': 'Sí' if row['volveria_visitar'] == 'si' else 'No',
                'area_mejora': row['area_mejora'],
                'calificacion_general': row['calificacion_general']
            })
        
    else:
        # Sin datos
        total_respuestas = 0
        promedio_calificacion = 0
        satisfaccion_servicio = 0
        tasa_retorno = 0
        datos_sucursales = []
        respuestas_tabla = []
    
    return render_template('reportes_admin.html',
                          paises=paises,
                          sucursales=sucursales,
                          pais_seleccionado=pais_seleccionado,
                          sucursal_seleccionada=sucursal_seleccionada,
                          fecha_inicio=fecha_inicio,
                          fecha_fin=fecha_fin,
                          total_respuestas=total_respuestas,
                          promedio_calificacion=promedio_calificacion,
                          satisfaccion_servicio=satisfaccion_servicio,
                          tasa_retorno=tasa_retorno,
                          datos_sucursales=datos_sucursales,
                          respuestas=respuestas_tabla)  # Enviar los datos de respuestas individuales
    
@app.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    """Ruta para solicitar recuperación de contraseña"""
    error = None
    mensaje = None
    
    # Verificar si el usuario fue redirigido tras intentos fallidos
    correo_redirect = session.get('correo_recuperacion', '')
    
    if request.method == 'POST':
        correo = request.form.get('email', '').strip()
        
        if not correo:
            error = "Por favor, ingresa tu correo electrónico"
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
            usuario = cur.fetchone()
            
            if usuario:
                # Generar código de verificación
                codigo = generar_codigo_verificacion()
                
                # Guardar código en la base de datos
                cur.execute("""
                UPDATE usuarios 
                SET codigo_verificacion = %s, fecha_codigo = NOW()
                WHERE correo = %s
                """, (codigo, correo))
                mysql.connection.commit()
                
                # Enviar correo con código
                if enviar_codigo_recuperacion(correo, codigo):
                    session['correo_recuperacion'] = correo
                    mensaje = "Se ha enviado un código de verificación a tu correo"
                    return redirect(url_for('verificar_codigo_recuperacion'))
                else:
                    error = "Error al enviar el código. Intenta nuevamente."
            else:
                error = "No existe una cuenta con ese correo electrónico"
            
            cur.close()
    
    # Si el usuario fue redirigido desde login por intentos fallidos y aún no se ha enviado el formulario
    elif correo_redirect and request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo_redirect,))
        usuario = cur.fetchone()
        
        if usuario:
            # Generar código de verificación
            codigo = generar_codigo_verificacion()
            
            # Guardar código en la base de datos
            cur.execute("""
            UPDATE usuarios 
            SET codigo_verificacion = %s, fecha_codigo = NOW()
            WHERE correo = %s
            """, (codigo, correo_redirect))
            mysql.connection.commit()
            
            # Enviar correo con código
            if enviar_codigo_recuperacion(correo_redirect, codigo):
                mensaje = f"Se ha enviado un código de verificación a {correo_redirect}"
                return redirect(url_for('verificar_codigo_recuperacion'))
            else:
                error = "Error al enviar el código. Intenta nuevamente."
        else:
            error = "No existe una cuenta con ese correo electrónico"
        
        cur.close()
    
    return render_template('recuperar_contrasena.html', error=error, mensaje=mensaje, correo_prefill=correo_redirect)


@app.route('/verificar_codigo_recuperacion', methods=['GET', 'POST'])
def verificar_codigo_recuperacion():
    """Ruta para verificar el código de recuperación"""
    error = None
    
    if 'correo_recuperacion' not in session:
        return redirect(url_for('recuperar_contrasena'))
    
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        correo = session.get('correo_recuperacion')
        
        if not codigo:
            error = "Por favor, ingresa el código de verificación"
        else:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT codigo_verificacion, fecha_codigo 
                FROM usuarios 
                WHERE correo = %s
            """, (correo,))
            resultado = cur.fetchone()
            
            if resultado and resultado[0] == codigo:
                # Verificar que el código no tenga más de 30 minutos
                tiempo_actual = datetime.now()
                tiempo_codigo = resultado[1]
                
                if tiempo_codigo and (tiempo_actual - tiempo_codigo).total_seconds() <= 1800:
                    # Marcar el código como verificado
                    session['codigo_verificado'] = True
                    return redirect(url_for('nueva_contrasena'))
                else:
                    error = "El código ha expirado. Solicita uno nuevo."
            else:
                error = "Código incorrecto. Intenta nuevamente."
            
            cur.close()
    
    return render_template('verificar_codigo_recuperacion.html', error=error)

@app.route('/nueva_contrasena', methods=['GET', 'POST'])
def nueva_contrasena():
    """Ruta para establecer nueva contraseña"""
    error = None
    
    if 'correo_recuperacion' not in session or 'codigo_verificado' not in session:
        return redirect(url_for('recuperar_contrasena'))
    
    if request.method == 'POST':
        correo = session.get('correo_recuperacion')
        nueva_contrasena = request.form.get('nueva_contrasena', '')
        confirmar_contrasena = request.form.get('confirmar_contrasena', '')
        
        if not nueva_contrasena or not confirmar_contrasena:
            error = "Por favor, completa todos los campos"
        elif nueva_contrasena != confirmar_contrasena:
            error = "Las contraseñas no coinciden"
        else:
            # Actualizar contraseña en la base de datos
            contrasena_hash = hash_password(nueva_contrasena)
            
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE usuarios 
                SET contraseña = %s, codigo_verificacion = NULL, fecha_codigo = NULL
                WHERE correo = %s
            """, (contrasena_hash, correo))
            mysql.connection.commit()
            cur.close()
            
            # Limpiar variables de sesión
            session.pop('correo_recuperacion', None)
            session.pop('codigo_verificado', None)
            
            flash("Tu contraseña ha sido actualizada exitosamente", "success")
            return redirect(url_for('login'))
    
    return render_template('nueva_contrasena.html', error=error)

@app.errorhandler(404)
def pagina_no_encontrada(error):
    """Manejador para errores 404"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def error_servidor(error):
    """Manejador para errores 500"""
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)