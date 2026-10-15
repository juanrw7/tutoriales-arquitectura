import unittest
from app import app


class FlaskTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_compra(self):
        response = self.client.post("/api/v2/comprar", json={"producto_id": 1, "cantidad": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Backend"], "Flask-v2")
        self.assertIn("procesada exitosamente por el Microservicio Flask", response.json["mensaje"])
        self.assertEqual(response.json["cantidad"], 2)

    def test_cantidad_predeterminada(self):
        self.assertEqual(self.client.post("/api/v2/comprar", json={"producto_id": 1}).json["cantidad"], 1)

    def test_falta_producto(self):
        self.assertEqual(self.client.post("/api/v2/comprar", json={}).status_code, 400)

    def test_identificador_invalido(self):
        for value in [0, -1, True, "1"]:
            self.assertEqual(self.client.post("/api/v2/comprar", json={"producto_id": value}).status_code, 400)

    def test_cantidad_invalida(self):
        for value in [0, -1, True, "1"]:
            self.assertEqual(self.client.post("/api/v2/comprar", json={"producto_id": 1, "cantidad": value}).status_code, 400)

    def test_json_invalido(self):
        for data in ['{', '[]', 'null']:
            self.assertEqual(self.client.post("/api/v2/comprar", data=data, content_type="application/json").status_code, 400)

    def test_tipo_contenido(self):
        self.assertEqual(self.client.post("/api/v2/comprar", data="producto_id=1").status_code, 415)

    def test_metodo_y_salud(self):
        self.assertEqual(self.client.get("/api/v2/comprar").status_code, 405)
        self.assertEqual(self.client.get("/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
