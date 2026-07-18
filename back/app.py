from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from consultas import cotizar_viaje


app = Flask(__name__)
CORS(app) #habilitacion de CORS

@app.route("/")
def inicio():
    #return "Servidor funcionando con Flask"
    return render_template("index.html")


@app.route("/cotizar", methods=["POST"])
def cotizar():

    datos = request.get_json()

    respuesta = cotizar_viaje(datos)
    
    return jsonify(respuesta)


if __name__ == "__main__":
    app.run(debug=True)