from .entities.User import User

class ModelUser:

    @classmethod
    def login(cls, db, user):
        try:
            cursor = db.connection.cursor()
            sql = """SELECT id_cliente_origen, name, contraseña FROM clientes 
                     WHERE name = %s AND contraseña = %s"""
            cursor.execute(sql, (user.name, user.contraseña))
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1], row[2])
            else:
                return None
        except Exception as ex:
            raise Exception(ex)
        
    @classmethod
    def get_by_id(cls, db, id):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT id_cliente_origen, name FROM clientes WHERE id_cliente_origen = %s"
            cursor.execute(sql, (id,))
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1], None)
            else:
                return None 
        except Exception as ex:
            raise Exception(ex)
