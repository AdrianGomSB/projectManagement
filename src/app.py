from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect 
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_paginate import Pagination, get_page_parameter
import MySQLdb.cursors
from config import config
from datetime import date
import joblib
import numpy as np
# import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, confusion_matrix

# Models
from models.ModelUser import ModelUser
from models.ModelProducto import ModelProducto

# Entities
from models.entities.User import User
from models.entities.Producto import Producto

app = Flask(__name__)
pkl_path = 'src/Api/'

def load_pkl_file(filepath):
    return joblib.load(filepath)

try:
    encoder_autoventa = load_pkl_file(pkl_path + 'encoder_autoventa.pkl')
    encoder_categoria = load_pkl_file(pkl_path + 'endocer_categoria.pkl')
    encoder_producto = load_pkl_file(pkl_path + 'endocer_producto.pkl')
    encoder_ventas = load_pkl_file(pkl_path + 'endocer_ventas.pkl')
    modelo_knn = load_pkl_file(pkl_path + 'modelo_knn_final.pkl')
except Exception as e:
    print(f"Error loading pickle files: {e}")
#____________________________________________________________________________________

# Función para manejar etiquetas nuevas
def transform_with_encoder(encoder, value):
    if value not in encoder.classes_:
        encoder.classes_ = np.append(encoder.classes_, value)
    return encoder.transform([value])[0]

csrf = CSRFProtect()
db = MySQL(app)
login_manager_app = LoginManager(app)

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    user_id = current_user.get_id()
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Obtener las transacciones del usuario logueado
    cursor.execute("SELECT * FROM transacciones WHERE id_cliente_origen = %s", (user_id,))
    transacciones = cursor.fetchall()

    # Si hay transacciones, obtener el valor de prediction_C2 de la primera transacción
    if transacciones:
        prediction_C2_value = transacciones[0]['prediction_C2']  # Asumiendo que prediction_C2 está en la columna 9
        print(f'El predictor es:{prediction_C2_value}')
        # Obtener transacciones basadas en prediction_C2
        cursor.execute("SELECT id_material_origen, des_categoria FROM transacciones WHERE prediction_C2 = %s", (prediction_C2_value,))
        print(f'El id es: {prediction_C2_value}')
        transacciones_prediction = cursor.fetchall()
        # Capturar productos con id_producto_origen sin repetición
        id_producto_origen_unicos = set()
        productos_sin_repeticion = []

        for transaccion in transacciones_prediction:
            id_producto_origen = transaccion['id_material_origen']  # Asegúrate de que el nombre de la columna sea correcto
            if id_producto_origen not in id_producto_origen_unicos:
                id_producto_origen_unicos.add(id_producto_origen)
                productos_sin_repeticion.append(transaccion)
                
        # Paginación
        page = request.args.get(get_page_parameter(), type=int, default=1)
        per_page = 20  # Número de elementos por página
        offset = (page - 1) * per_page
        total = len(productos_sin_repeticion)
        productos_paginated = productos_sin_repeticion[offset: offset + per_page]
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

        return render_template('home.html', transacciones=productos_paginated, pagination=pagination)
    else:
        
        return render_template('home.html', transacciones=[], pagination=None)

@app.route('/listar')
@login_required
def table():
    user_id = current_user.get_id()

    cursor = db.connection.cursor()
    cursor.execute("SELECT id_transacciones, id_cliente_origen, id_material_origen, cod_categoria, des_categoria, tier_producto, des_fuerza_ventas, ind_autoventa FROM transacciones WHERE id_cliente_origen = %s", (user_id,))
    data = cursor.fetchall()
    return render_template('lista.html', data=data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(0, username, password)
        logged_user = ModelUser.login(db, user)
        if logged_user:
            login_user(logged_user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form['name']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            if password != confirm_password:
                flash('Passwords does not match.')
                return redirect(url_for('register'))

            cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM clientes WHERE name = %s', (name,))
            account = cursor.fetchone()

            if account:
                flash('The username is already in use.')
                return redirect(url_for('register'))

            rol = 0  # Asignar rol 0 por defecto
            cursor.execute('INSERT INTO clientes (name, contraseña, rol) VALUES (%s, %s, %s)', (name, password, rol))
            db.connection.commit()
            flash('Successful registration. Please log in.')
            return redirect(url_for('login'))
        except KeyError as e:
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/new_transaction', methods=['GET', 'POST'])
@login_required
def new_transaction():
    if request.method == 'POST':
        try:
            id_cliente_origen = current_user.get_id()
            id_material_origen = int(request.form['id_material_origen'])
            cod_categoria = float(request.form['cod_categoria'])
            des_categoria = request.form['des_categoria']
            tier_producto = request.form['tier_producto']
            des_fuerza_ventas = request.form['des_fuerza_ventas']
            ind_autoventa = request.form['ind_autoventa']
            monto = float(request.form['monto'])

            # Validar que todos los campos requeridos tienen valores
            if not (id_material_origen and cod_categoria and des_categoria and tier_producto and des_fuerza_ventas and ind_autoventa and monto):
                return redirect(url_for('new_transaction'))

            # Transformar los datos utilizando los encoders
            encoded_input = [
                id_cliente_origen,
                id_material_origen,
                cod_categoria,
                transform_with_encoder(encoder_categoria, des_categoria),
                transform_with_encoder(encoder_producto, tier_producto),
                transform_with_encoder(encoder_ventas, des_fuerza_ventas),
                transform_with_encoder(encoder_autoventa, ind_autoventa),
                monto
            ]

            # Asegurarnos de que todos los valores sean numéricos
            encoded_input = [float(value) for value in encoded_input]

            # Realizar la predicción
            prediction = modelo_knn.predict([encoded_input])[0]

            cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO transacciones (id_cliente_origen, id_material_origen, cod_categoria, des_categoria, tier_producto, des_fuerza_ventas, ind_autoventa, monto, fec_documento, prediction_C2) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (id_cliente_origen, id_material_origen, cod_categoria, des_categoria, tier_producto, des_fuerza_ventas, ind_autoventa, monto, date.today(), prediction))
            db.connection.commit()

            return redirect(url_for('home'))
        except ValueError as ve:
            return redirect(url_for('new_transaction'))
        except Exception as e:
            return redirect(url_for('new_transaction'))

    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id_material_origen, cod_categoria, des_categoria, tier_producto FROM productos')
    productos = cursor.fetchall()

    # Filtrar productos para asegurarse de que no tengan valores None
    productos = [p for p in productos if None not in p.values()]
    # Lista de valores ordenados
    values = sorted([559, 416, 418, 421, 417, 427, 426, 415, 422, 419, 430, 414, 413, 424, 425, 431, 433, 420, 423, 434, 428, 429, 442, 440, 435, 432, 465, 467, 492, 469, 493, 471, 494, 476, 481, 482, 497, 484, 485, 486, 466, 473, 477, 496, 512, 511, 117, 106, 113, 189, 124, 121, 128, 127, 135, 139, 142, 183, 148, 151, 152, 154, 155, 112, 116, 111, 109, 126, 122, 129, 132, 120, 137, 140, 138, 144, 150, 103, 105, 130, 166, 136, 175, 146, 169, 163, 108, 119, 133, 167, 143, 145, 159, 153, 170, 99, 100, 180, 162, 164, 123, 134, 161, 165, 131, 102, 98, 107, 125, 118, 157, 168, 110, 114, 158, 174, 2, 3, 4, 6, 8, 9, 11, 16, 19, 21, 22, 23, 24, 26, 27, 28, 31, 32, 30, 35, 39, 41, 17, 38, 44, 47, 50, 40, 10, 49, 12, 52, 7, 57, 5, 18, 60, 36, 48, 64, 59, 68, 55, 70, 71, 73, 75, 945, 952, 989, 942, 955, 943, 967, 958, 982, 968, 964, 948, 962, 963, 953, 954, 959, 975, 946, 961, 949, 970, 981, 992, 977, 941, 1015, 1017, 1016, 995, 996, 1002, 1011, 1003, 998, 1055, 1054, 1058, 1047, 1046, 1049, 1048, 1057, 1062, 1060, 1045, 1051, 1061, 1059, 1050, 1053, 1056, 1063, 1052, 1064, 564, 567, 571, 569, 574, 575, 576, 577, 578, 580, 581, 579, 745, 747, 748, 749, 744, 752, 753, 754, 756, 758, 755, 759, 760, 762, 763, 765, 764, 767, 769, 768, 766, 772, 773, 771, 770, 221, 228, 229, 230, 231, 232, 234, 235, 236, 237, 238, 239, 240, 241, 242, 244, 233, 245, 246, 247, 248, 250, 251, 249, 252, 253, 254, 256, 259, 227, 255, 261, 243, 260, 258, 263, 264])
    fuerza_ventas_values = sorted(['FFVV_13', 'FFVV_5', 'FFVV_9', 'FFVV_15', 'FFVV_3', 'FFVV_11', 'FFVV_16', 'FFVV_20', 'FFVV_12', 'FFVV_25', 'FFVV_14', 'FFVV_10', 'FFVV_18', 'FFVV_8', 'FFVV_23', 'FFVV_1', 'FFVV_2', 'FFVV_6', 'FFVV_4', 'FFVV_7', 'FFVV_22', 'FFVV_24', 'FFVV_30', 'FFVV_28', 'FFVV_26'])

    return render_template('compra.html', values=values, fuerza_ventas_values=fuerza_ventas_values, productos=productos)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados. </h1>"

def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1>Página no encontrada. </h1>", 404

if __name__ == '__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run()
