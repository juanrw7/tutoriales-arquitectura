# Tutorial 06 - Primer estrangulamiento: Django v1 y Flask v2

Estudiante: Juan Manuel Ramirez.
Estado: implementacion y enrutamiento comprobados localmente; despliegue y
capturas de Postman en AWS pendientes de configurar el entorno.

## Entregable exigido por el PDF

La seccion 7 pide **un documento PDF** con:
1. Captura de Postman haciendo GET a http://IP-AWS/api/v1/productos/, respondido
   por Django.
2. Captura de Postman haciendo POST a http://IP-AWS/api/v2/comprar, con el mensaje
   de compra procesada exitosamente por el Microservicio Flask.
3. Salida de docker compose logs nginx donde se vean peticiones a los dos backends.

El borrador incluido tiene esas tres secciones, claramente marcadas como pendientes.
No es el documento final para entregar. No se han sustituido las capturas de AWS
por imagenes locales ni se han inventado registros.

## Paso 1 - Microservicio

microservicio_pagos/app.py contiene la aplicacion Flask y la ruta POST
/api/v2/comprar. Recibe un objeto JSON con producto_id y cantidad (por defecto 1).
Devuelve HTTP 200 y:
```json
{
  "mensaje": "Compra procesada exitosamente por el Microservicio Flask (v2)",
  "producto_id": 1,
  "cantidad": 2,
  "status": "Aprobado"
}
```

Se validan JSON, tipo de contenido, identificador y cantidad. Devuelve 400 para
JSON/datos invalidos y 415 si el contenido no es JSON. /health permite el healthcheck.
X-Backend: Flask-v2 identifica el destino de la peticion.

Como en el ejemplo del PDF, v2 es una simulacion de negocio: no consulta la base
PostgreSQL, no descuenta stock ni realiza cobros. La compra real del monolito se
conserva en v1. Esto demuestra extraccion y enrutamiento, no una migracion completa
de persistencia o pagos distribuidos.

## Completar el catalogo v1 requerido

El tutorial solicita /api/v1/productos/, pero esa ruta no existia en el proyecto
anterior. Se agrego ProductosAPIView, que utiliza LibroSerializer para devolver
id, titulo, precio y stock_actual desde la base de datos del monolito.
La cabecera X-Backend: Django-v1 identifica su respuesta.

No se modifico CompraService. Se conservan /api/v1/comprar/, las vistas HTML,
el inventario, el endpoint de salud y los estilos de DRF.

## Paso 2 - Dockerfile del microservicio

microservicio_pagos/Dockerfile usa python:3.11-alpine, instala versiones fijadas
por su propio requirements.txt y ejecuta Gunicorn app:app en 0.0.0.0:5000.
El monolito mantiene su Dockerfile y sus dependencias independientes.
Los paquetes del microservicio se comprobaron para Python 3.11 y musllinux x86_64;
esto no sustituye la construccion real de la imagen con Docker.

## Paso 3 - Compose

Cuatro servicios: db, web_django, pagos_flask y nginx.
El nombre web se cambio a web_django para coincidir con el ejemplo y el upstream.
Django usa el modulo real Tienda.wsgi:application.

En la receta final solo Nginx publica 80:80. Django y Flask tienen expose 8000
y 5000, respectivamente, sin publicar esos puertos en el host. PostgreSQL sigue
en la red database interna; ambos servidores HTTP se conectan a edge.
Se conservan postgres_data y payments_data y las esperas por healthchecks.

El PDF abre 5000 temporalmente para probar. Se proporciona esa etapa en una receta
separada, docker-compose.pruebas.yml, que publica solo 127.0.0.1:5000:5000:
```powershell
docker compose -f docker-compose.yml -f docker-compose.pruebas.yml up -d --build
```

En esa prueba local, Postman puede enviar el POST directamente a
http://localhost:5000/api/v2/comprar. Para volver a la receta final y cerrar el
mapeo temporal, ejecutar la receta base recreando los contenedores:
```powershell
docker compose up -d --build --remove-orphans --force-recreate
```

No agregar reglas publicas 5000 en AWS para la arquitectura final.

## Paso 4 - Nginx y trazabilidad

nginx/nginx.conf tiene dos upstreams:
- django_v1 -> web_django:8000.
- flask_v2 -> pagos_flask:5000.

location /api/v1/ envia las peticiones a Django; location /api/v2/comprar las envia
a Flask. proxy_pass no agrega una barra final, por lo que mantiene la ruta completa
que esperan ambos backends. El resto de las paginas del monolito sigue en Django.

El log_format routing agrega upstream=$proxy_host, addr=$upstream_addr y
upstream_status=$upstream_status. De esta manera, docker compose logs nginx muestra
el nombre del destino y su puerto, en lugar de limitarse a registrar la URL publica.
La imagen oficial de Nginx envia su access.log a la salida del contenedor.

No se usa Flask para responder /api/v1/ ni se elimina el monolito: ambas versiones
coexisten en el mismo dominio, y Nginx selecciona el destino.

## Ejecutar localmente en Windows

Con Docker Desktop abierto, entrar a la carpeta que contiene manage.py:
```powershell
py scripts\crear_env.py
docker compose config --quiet
docker compose up -d --build --remove-orphans --force-recreate
docker compose ps
docker compose exec nginx nginx -t
```

Si .env ya existe, conservar sus secretos; el generador no lo sobrescribe.
Probar en Postman, a traves de Nginx:

| Peticion | URL local | Cuerpo |
|---|---|---|
| GET v1 | http://localhost/api/v1/productos/ | Sin cuerpo |
| POST v2 | http://localhost/api/v2/comprar | JSON con producto_id y cantidad |
| POST compra v1 | http://localhost/api/v1/comprar/ | JSON con libro_id y direccion_envio |

Para v2, Body > raw > JSON:
```json
{"producto_id": 1, "cantidad": 2}
```

Headers: Content-Type: application/json. Comprobar HTTP 200 y el mensaje de Flask.
Para comprobar los logs:
```powershell
docker compose logs nginx
```

## Paso 5 - Actualizar AWS, cuando configuremos el entorno

Completar primero las evidencias pendientes del 04 y 05. Luego aplicar esta etapa
al MISMO proyecto Compose, conservando su carpeta y .env para mantener los volumenes.
Si se utiliza Git, guardar estos cambios en tu propio repositorio y hacer push;
no se ha realizado un push por ti.

En EC2:
```bash
cd TU-CARPETA-ACTUAL
git pull origin main
bash scripts/desplegar_ec2.sh
docker compose ps
docker compose exec nginx nginx -t
docker compose logs web_django pagos_flask nginx
```

Usar la rama real de tu repositorio si no es main. Como alternativa, transferir
el ZIP y copiar su contenido a la carpeta existente, como se explica en las guias
anteriores; el ZIP no contiene .env ni .git.

El script fuerza recreacion para que Nginx lea su configuracion nueva y elimina
el antiguo contenedor web, ahora sustituido por web_django. Los volumenes con datos
se conservan; el reinicio produce una interrupcion breve del servicio.

Security Group: HTTP 80 abierto, SSH segun tu conexion y sin reglas publicas 8000,
5000 o 5432. DJANGO_ALLOWED_HOSTS debe incluir la IP publica actual de EC2.

## Tomar las evidencias en Postman

1. GET http://IP-PUBLICA/api/v1/productos/. Mostrar URL, metodo, HTTP 200 y lista
   JSON de libros. Guardar captura como evidencia/v1_postman_aws.png.
2. POST http://IP-PUBLICA/api/v2/comprar, Body > raw > JSON:
   {"producto_id": 1, "cantidad": 2}. Mostrar URL, metodo, HTTP 200 y mensaje de
   Flask. Guardar captura como evidencia/v2_postman_aws.png.
3. En EC2, despues de esas peticiones:
```bash
docker compose logs --no-color nginx > nginx_aws.log
```

El archivo debe incluir las dos peticiones y los destinos django_v1:8000 y
flask_v2:5000. Descargarlo y guardarlo como evidencia/nginx_aws.log junto a las
capturas. No usar LOGS_PROXY_LOCAL.txt para acreditar el despliegue de AWS.

## Generar el PDF final

El generador usa los archivos reales que se proporcionen. Primero instalar sus
dependencias en el entorno Python del equipo:
```powershell
py -m pip install -r scripts\requirements_informe.txt
```

Desde la carpeta del proyecto, reemplazando IP-PUBLICA por la IP real:
```powershell
py scripts\generar_informe06.py --ip IP-PUBLICA --v1 evidencia\v1_postman_aws.png --v2 evidencia\v2_postman_aws.png --logs evidencia\nginx_aws.log --output Informe_Tutorial06_JUAN_MANUEL_RAMIREZ.pdf
```

El script valida que la IP sea publica, que las capturas sean imagenes y que los
logs contengan los dos destinos con sus puertos. No sobrescribe un PDF existente.
Estas validaciones no comprueban por si solas el contenido visual de Postman:
revisar las capturas y cada pagina del PDF antes de subirlo a la plataforma.
El PDF final incluye ambas capturas y la salida de logs completa, con paginas
adicionales si es necesario. La entrega obligatoria es ese PDF, no el ZIP.

## Revision realizada

- 42 pruebas de Django y 8 de Flask aprobadas: total 50.
- Django check sin problemas y sin migraciones pendientes.
- Compose base y etapa de prueba validables sin ejecutar contenedores.
- Nginx y ambos Gunicorn ejecutados como procesos locales reales.
- GET v1 productos: 200, X-Backend Django-v1 y catalogo correcto.
- POST v2 compra: 200, X-Backend Flask-v2 y mensaje esperado.
- Logs locales con ambos upstreams.
- Compra v1 conservada: 201 y stock 10 -> 9.
- Se comprobo que la simulacion v2 no altera el inventario de Django.
- Borrador PDF revisado visualmente.

Las pruebas del proxy usan SQLite y puertos temporales locales; no son ejecucion
en Docker o AWS. Se conserva el resultado en VERIFICACION_PROXY_LOCAL.json y
LOGS_PROXY_LOCAL.txt, marcados como locales.

Pendientes: construir las imagenes, ejecutar Compose/PostgreSQL, desplegar en EC2,
tomar capturas reales de Postman y generar/revisar el PDF final. Como acordamos,
esos pasos se haran cuando configuremos el entorno.
