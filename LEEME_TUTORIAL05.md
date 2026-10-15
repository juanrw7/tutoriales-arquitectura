# Tutorial 05 - Nginx, Gunicorn y base del Strangler Pattern

Estudiante: Juan Manuel Ramirez.
Estado: implementacion preparada y comprobada localmente; Docker/EC2 y capturas
finales pendientes de configurar el entorno, como se acordo.

## Entrega de Resultados - tres capturas

El PDF exige tres archivos de evidencia:

| Evidencia | Contenido que debe verse | Nombre sugerido |
|---|---|---|
| Navegador | API desde http://IP-EC2/api/v1/comprar/, sin :8000, con respuesta JSON | 01_API_Nginx_AWS_JUAN_MANUEL_RAMIREZ.png |
| Terminal local | Intento a http://IP-EC2:8000/ que falla por timeout | 02_Aislamiento_8000_JUAN_MANUEL_RAMIREZ.png |
| Terminal AWS | docker ps con nginx, web y db en estado Up | 03_Docker_PS_AWS_JUAN_MANUEL_RAMIREZ.png |

Todavia no se generaron esas capturas porque no se ha desplegado en tu cuenta AWS.
Este ZIP y la guia sirven para completar la practica; no sustituyen las capturas.
El PDF no especifica el nombre de la asignacion.

## Paso 1 - Gunicorn

requirements.txt incluye gunicorn==26.2.0. Se mantiene Django 5.2.18 del proyecto
existente; el ejemplo del PDF muestra Django 4.x, pero no es necesario bajar su
version para usar Gunicorn en este proyecto.

Se sustituyo runserver en Dockerfile y Compose por:
```bash
gunicorn Tienda.wsgi:application --bind 0.0.0.0:8000 --workers 2 --access-logfile - --error-logfile -
```

El modulo real es Tienda.wsgi, no tienda_project.wsgi del ejemplo.
entrypoint.sh sigue aplicando migraciones, recolectando estaticos y creando los
libros de prueba antes de ejecutar Gunicorn. El servicio de negocio se conserva.

## Paso 2 - Nginx

nginx/nginx.conf configura:
- upstream django_backend dirigido a web:8000.
- listen 80, unica entrada HTTP publicada.
- location / que reenvia la URL completa al backend, sin quitar /api/v1/.
- Cabeceras Host, X-Forwarded-For, X-Real-IP y X-Forwarded-Proto.
- Favicon sin registros innecesarios y configuracion montada como solo lectura.

Se eligio nginx:1.30.5-alpine, una etiqueta oficial verificada, en lugar de la
version 1.25 del ejemplo. Las directivas usadas conservan el comportamiento pedido.
WhiteNoise sigue sirviendo los estilos de DRF desde Django con DEBUG=0.

Esta es la base del Strangler Pattern: posteriormente se puede agregar una
location /api/v2/ para desviar esas peticiones a Flask. En este tutorial no se
habilita una ruta hacia un microservicio inexistente ni se reemplaza /api/v1/.

## Paso 3 - Compose y aislamiento

Tres servicios: db, web y nginx.

- db: PostgreSQL 15, volumen persistente y healthcheck; sin puerto publicado.
- web: Gunicorn, expose 8000, sin ports. La instruccion expose es informacion para
  la red del contenedor; no publica 8000 en el equipo anfitrion.
- nginx: publica exclusivamente 80:80 y espera a que web este saludable.

Hay una red edge para Nginx/web y una red database interna para web/db.
Se conservan postgres_data y payments_data. /health/ devuelve status ok sin
consultar la base de datos y permite verificar la disponibilidad de Gunicorn.

## Prueba local en Windows

Docker Desktop debe estar abierto, con contenedores Linux.
En la carpeta que contiene manage.py y Dockerfile:

```powershell
py scripts\crear_env.py
docker compose config --quiet
docker compose up -d --build --remove-orphans
docker compose ps
docker compose logs web nginx
docker compose exec nginx nginx -t
```

Si ya existe .env, crear_env.py se detiene sin sobrescribirlo. Mantener sus secretos.
Si el puerto 80 esta ocupado por otro programa, detener ese programa antes de
levantar Nginx. La practica pide usar 80, no sustituirlo en la captura final.

Abrir http://localhost/api/v1/comprar/. El GET inicial devuelve 405 porque la API
acepta POST, pero debe mostrar el formulario de DRF.
Raw data > application/json:
```json
{
  "libro_id": 1,
  "direccion_envio": "Medellin - Juan Manuel Ramirez",
  "cantidad": 1
}
```

Pulsar POST; comprobar HTTP 201 Created y total 178.50.
Abrir http://localhost/inventario/ para ver el descuento de stock.
Para comprobar el servidor WSGI y la configuracion:
```powershell
docker compose exec web python manage.py check
docker compose exec web python manage.py test tienda_app
docker compose exec web cat /app/logs/pagos_locales_JUAN_MANUEL_RAMIREZ.log
```

Con esta receta no se debe usar localhost:8000 para entrar a Django desde el host.

## Paso 4 - Actualizar la instancia del tutorial 04

Primero hay que completar la configuracion del entorno y tomar la captura de AWS
del tutorial 04. Despues se cambia a esta arquitectura y se toman estas evidencias.

### Si usas tu propio repositorio Git

Aplicar los archivos a tu repositorio, comprobar git status y guardar los cambios:
```bash
git add Dockerfile docker-compose.yml requirements.txt nginx tienda_app/views.py tienda_app/urls.py tienda_app/test_salud.py scripts LEEME_TUTORIAL05.md
git commit -m "Usar Nginx y Gunicorn con backend interno"
git push origin main
```

Usar main solo si es la rama real de tu repositorio. No se ha realizado un push
por ti: falta conectar tu propio repositorio. No subir .env ni claves privadas.

En EC2 Instance Connect/SSH, entrar a la misma carpeta del proyecto del tutorial 04:
```bash
cd TU-CARPETA-DEL-PROYECTO
git pull origin main
bash scripts/desplegar_ec2.sh
docker compose ps
docker compose exec nginx nginx -t
docker compose logs web nginx
```

### Si transfieres el ZIP

Se puede transferir por SCP con tu clave, como se explica en la guia del tutorial 04.
Si ya hay un despliegue del 04, copiar los archivos nuevos a su MISMA carpeta y
conservar .env. No levantar el 05 como otro proyecto mientras el 04 sigue publicado
por 8000. Mantener la carpeta y el nombre de proyecto Compose conserva los volumenes
y actualiza el servicio existente, eliminando su antiguo mapeo 8000:8000.

Ejemplo en EC2, despues de transferir el ZIP:
```bash
unzip Proyecto_Tutorial05_PREPARADO_JUAN_MANUEL_RAMIREZ.zip -d /tmp/tutorial05-preparado
cp -a /tmp/tutorial05-preparado/Tutorial05_JUAN_MANUEL_RAMIREZ/. /home/ec2-user/TU-CARPETA-ACTUAL/
cd /home/ec2-user/TU-CARPETA-ACTUAL
bash scripts/desplegar_ec2.sh
```

Sustituir TU-CARPETA-ACTUAL por la carpeta usada en el tutorial 04. El ZIP no
contiene .env, por lo que no reemplaza ese archivo. Tampoco contiene .git.
Si es un despliegue desde cero, se puede usar la carpeta extraida y generar .env;
ese primer arranque tendra una base PostgreSQL nueva con stock 10 por libro.

Mantener DJANGO_ALLOWED_HOSTS con la IP publica actual de EC2, localhost y 127.0.0.1.

## Paso 4.1 - Security Group

EC2 > Security Groups > grupo de la instancia > Edit inbound rules:
1. Agregar HTTP, TCP 80, origen 0.0.0.0/0, como indica el PDF.
2. Quitar la regla Custom TCP 8000 que se abrio para el tutorial 04.
3. Mantener el acceso SSH necesario para tu conexion.
4. Guardar.

Cerrar la regla 8000 ayuda a obtener el timeout que el PDF solicita; quitar ports
del servicio web es lo que elimina su publicacion en Docker. Se aplican ambas
medidas. Un timeout por si solo no prueba que los contenedores esten sanos:
comprobar primero que la API funciona por 80 y que los tres contenedores estan Up.

## Como tomar las tres capturas

### 1. Navegador

Abrir `http://IP-PUBLICA/api/v1/comprar/`, sin :8000. Enviar el JSON por POST desde
DRF. Capturar la barra de direcciones y HTTP 201 Created con la respuesta de exito.
No usar una captura de localhost como evidencia de AWS.

### 2. Terminal local de Windows

En PowerShell:
```powershell
.\scripts\verificar_aislamiento.ps1 -PublicIp IP-PUBLICA
```

El script comprueba primero /health/ por 80 y luego hace un intento real al 8000.
Si tu politica de ejecucion no permite scripts, ejecutar directamente:
```powershell
curl.exe --fail --max-time 10 http://IP-PUBLICA/health/
curl.exe --verbose --connect-timeout 5 --max-time 10 http://IP-PUBLICA:8000/
```

Sustituir IP-PUBLICA. Se espera curl: (28), timeout. Capturar el comando, la IP y
el error. Si aparece conexion rechazada, el puerto tampoco es accesible, pero
el PDF exige timeout: revisar que el Security Group ya no permita el 8000.

### 3. Terminal AWS

En la consola de la instancia:
```bash
docker ps
```

Tomar una captura legible de las filas nginx, web y db, todas Up. En PORTS, Nginx
debe mostrar el mapeo del puerto 80. web puede mostrar 8000/tcp como puerto interno,
pero no debe aparecer un mapeo del host como 0.0.0.0:8000->8000/tcp.

No detener los contenedores antes de tomar las capturas. Conservar los datos que
necesites y detener el laboratorio al finalizar, segun las indicaciones de Academy.

## Verificacion realizada y limites

Se comprobaron:
- 39 pruebas de aplicacion aprobadas (37 anteriores y 2 del endpoint de salud).
- Django check sin problemas.
- Docker Compose config correcto, sin publicar 8000 en web ni 5432 en db.
- Sintaxis Python/shell/YAML y generacion de .env.
- Nginx 1.30.5 y Gunicorn 26.2.0 ejecutados realmente como procesos locales.
- POST por Nginx: 201, total 178.50, inventario 10 -> 9 y un registro de pago.
- Endpoint de salud y CSS de DRF accesibles por el proxy.

Para esa prueba se sustituyeron los puertos de la receta por puertos temporales de
loopback y se uso SQLite temporal. Se valido el enrutamiento con nginx -t en una
configuracion local que conserva el fragmento del proyecto, adaptando su upstream
al proceso Gunicorn local. No es una prueba de redes Docker ni de seguridad AWS.

Pendientes: build/up reales en Docker, compra con PostgreSQL del contenedor,
despliegue en EC2, comprobacion externa del aislamiento y las tres capturas AWS.
No se incluye evidencia ficticia para marcar esos pasos como completados.

## Referencias oficiales

- [Directivas del proxy de Nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Version estable de Nginx](https://nginx.org/en/download.html)
- [Etiquetas oficiales de la imagen](https://github.com/docker-library/official-images/blob/master/library/nginx)
- [Orden de arranque de Compose](https://docs.docker.com/compose/how-tos/startup-order/)
