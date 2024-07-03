class Config:
    SECRET_KEY = 'B!1weNAt1T^%kvhUI*S^'


class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'pokemonblack2'
    MYSQL_DB = 'capstone'




config={
    'development':DevelopmentConfig
}