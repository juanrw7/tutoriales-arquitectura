from flask import Flask, jsonify, request

app = Flask(__name__)


@app.after_request
def identificar_backend(response):
    response.headers["X-Backend"] = "Flask-v2"
    return response


@app.get("/health")
def salud():
    return jsonify({"status": "ok", "backend": "Flask-v2"})


@app.route("/api/v2/comprar", methods=["POST"], strict_slashes=False)
def realizar_compra():
    # Simulacion academica del PDF: no cobra ni modifica inventario.
    if not request.is_json:
        return jsonify({"error": "Se requiere Content-Type application/json"}), 415
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "El cuerpo debe ser un objeto JSON valido"}), 400
    producto_id = data.get("producto_id")
    cantidad = data.get("cantidad", 1)
    if producto_id is None:
        return jsonify({"error": "Falta el ID del producto"}), 400
    if type(producto_id) is not int or producto_id <= 0:
        return jsonify({"error": "producto_id debe ser un entero positivo"}), 400
    if type(cantidad) is not int or cantidad <= 0:
        return jsonify({"error": "cantidad debe ser un entero positivo"}), 400
    return jsonify({
        "mensaje": "Compra procesada exitosamente por el Microservicio Flask (v2)",
        "producto_id": producto_id,
        "cantidad": cantidad,
        "status": "Aprobado",
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
