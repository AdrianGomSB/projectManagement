from .entities.Producto import Producto

class ModelProducto:

    @classmethod
    def get_productos_by_prediction_C2(self, db, prediction_C2):
        try:
            cursor = db.connection.cursor()
            sql = """SELECT id_transacciones, id_cliente_origen, id_material_origen, cod_categoria, 
                     des_categoria, tier_producto, des_fuerza_ventas, ind_autoventa, prediction_C2 
                     FROM transacciones WHERE prediction_C2 = %s"""
            cursor.execute(sql, (prediction_C2,))
            row = cursor.fetchall()
            if row:
                return Producto(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
            else:
                return None

        except Exception as ex:
            raise Exception(ex)
