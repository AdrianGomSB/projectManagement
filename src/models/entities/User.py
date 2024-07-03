from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id_cliente_origen, name, contraseña) -> None:
        self.id_cliente_origen = id_cliente_origen
        self.name = name
        self.contraseña = contraseña

    def get_id(self):
        return str(self.id_cliente_origen)

    def __repr__(self):
        return f"User(id_cliente_origen={self.id_cliente_origen}, name={self.name}, contraseña={self.contraseña})"
