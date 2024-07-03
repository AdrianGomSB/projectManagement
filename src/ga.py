from sqlalchemy import create_engine

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sqlalchemy import create_engine
import pandas as pd
import joblib

# Configuración de la conexión a MySQL
db_user = 'root'
db_password = 'pokemonblack2'
db_host = 'localhost'
db_name = 'capstone'

# Crear la cadena de conexión
engine = create_engine(f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}')

# Consultar los datos de MySQL
query = 'SELECT * FROM transacciones'
data = pd.read_sql(query, engine)

# Preprocesamiento de datos
data = data.drop(columns=['fec_documento'])

label_encoders = {}
for column in ['des_categoria', 'tier_producto', 'des_fuerza_ventas', 'ind_autoventa']:
    le = LabelEncoder()
    data[column] = le.fit_transform(data[column])
    label_encoders[column] = le

X = data.drop('prediction_C2', axis=1)
y = data['prediction_C2']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=42)

# Entrenar el modelo KNN
knn = KNeighborsClassifier(n_neighbors=6)
knn.fit(X_train, y_train)

# Guardar el modelo y los encoders
joblib.dump(knn, 'src/modelo.pkl')
joblib.dump(scaler, 'src/scaler.pkl')
joblib.dump(label_encoders, 'src/label_encoders.pkl')