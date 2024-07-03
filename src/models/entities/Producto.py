from flask_login import UserMixin

class Producto:
    def __init__(self, id_transacciones, id_cliente_origen, id_material_origen, cod_categoria, des_categoria, tier_producto, des_fuerza_ventas, ind_autoventa, prediction_C2):
        self.id_transacciones = id_transacciones
        self.id_cliente_origen = id_cliente_origen
        self.id_material_origen = id_material_origen
        self.cod_categoria = cod_categoria
        self.des_categoria = des_categoria
        self.tier_producto = tier_producto
        self.des_fuerza_ventas = des_fuerza_ventas
        self.ind_autoventa = ind_autoventa
        self.prediction_C2 = prediction_C2
