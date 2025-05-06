import pandas as pd
import matplotlib.pyplot as plt
from flask import Blueprint, jsonify
from app import mysql

reportes = Blueprint('reportes', __name__)

@reportes.route('/estadisticas', methods=['GET'])
def generar_estadisticas():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT respuesta FROM respuestas")
    data = cursor.fetchall()
    
    df = pd.DataFrame(data, columns=['respuesta'])
    grafico = df['respuesta'].value_counts().plot(kind='bar')
    plt.savefig("static/estadisticas.png")
    
    return jsonify({"mensaje": "Estadísticas generadas"})
