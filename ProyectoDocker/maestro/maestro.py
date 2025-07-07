from flask import Flask, request
import datetime

app = Flask(__name__)

@app.route("/resultado", methods=["POST"])
def recibir_resultado():
    data = request.get_json()

    linea = f"{datetime.datetime.now()}, {data['esclavo']}, {data['algoritmo']}, {data['resolucion']}, {data['iteraciones']}, {data['tiempo']}s\n"
    
    print("[Maestro] Recibido:", linea.strip())

    with open("resultados.txt", "a") as f:
        f.write(linea)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
