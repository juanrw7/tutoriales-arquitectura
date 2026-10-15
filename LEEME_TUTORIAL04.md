# Tutorial 04 - Docker y AWS EC2

Estudiante: Juan Manuel Ramirez.
Estado: proyecto preparado; despliegue real y captura de AWS pendientes.

## Que pide la entrega

El PDF principal, tutorial04_Docker_AWS.pdf, solicita una **captura del navegador**
accediendo a `http://IP-PUBLICA-EC2:8000/api/v1/comprar/`, con la respuesta JSON
servida desde AWS. Debe verse la direccion publica de la instancia.

No solicita subir un ZIP, Dockerfile, log o informe como evidencia obligatoria.
Este proyecto es el material para ejecutar el laboratorio. La captura debe tomarse
cuando el despliegue real este funcionando; no se incluye una imagen local como
si proviniera de AWS.

El PDF tutorial04-B-AWS.pdf tiene otra ruta: esta rotulado como tutorial 05,
menciona Laravel, RDS MySQL y un curso de 2025. Sus diferencias se explican en
`docs/Comparacion_04B_AWS.md`. Para esta Tienda API se sigue el PDF principal:
Django + PostgreSQL + Docker Compose + EC2, en el puerto 8000.

## Paso 1 - Configuracion

Tienda/settings.py obtiene del entorno DB_NAME, DB_USER, DB_PASSWORD, DB_HOST,
DB_PORT, DJANGO_SECRET_KEY, DJANGO_DEBUG y DJANGO_ALLOWED_HOSTS. DB_PASSWORD y
DJANGO_SECRET_KEY no tienen credenciales de respaldo en el codigo.

requirements.txt se genero con pip freeze desde un entorno dedicado. Incluye
psycopg2-binary, DRF, Django, Markdown, django-filter, WhiteNoise y PyYAML.
WhiteNoise sirve los estilos de DRF cuando DEBUG=0; PyYAML se usa en el verificador.
El servicio de compra del tutorial 03 se conserva sin cambios.

.env.example sirve como plantilla. `scripts/crear_env.py` genera una contrasena
de base de datos y una clave Django diferentes, sin mostrarlas por consola.
No sobrescribe un .env existente. .env esta excluido de Git y del contexto Docker.

## Paso 2 - Dockerfile

El Dockerfile esta en la raiz, junto a manage.py. Usa python:3.11-slim,
PYTHONDONTWRITEBYTECODE=1, PYTHONUNBUFFERED=1, /app como WORKDIR y la instalacion
por requirements.txt antes de copiar el codigo.

entrypoint.sh exige las variables, aplica migrate, ejecuta collectstatic, crea
los tres libros de prueba de forma idempotente y arranca el CMD con exec.
CMD ejecuta `python manage.py runserver 0.0.0.0:8000 --noreload`, como laboratorio.
El .dockerignore evita copiar secretos, bases SQLite, logs y archivos temporales.

## Paso 3 - Prueba local en Windows

1. Instalar y abrir Docker Desktop, usando contenedores Linux.
2. Descomprimir y entrar a la carpeta que contiene manage.py y Dockerfile.
3. Abrir PowerShell en esa carpeta y ejecutar:

```powershell
py scripts\crear_env.py
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs web
```

La web depende del healthcheck de PostgreSQL. El puerto de PostgreSQL no se
publica en el host; Django lo encuentra por DB_HOST=db dentro de Compose.
Los datos se guardan en postgres_data y los pagos en payments_data.

4. Abrir http://localhost:8000/api/v1/comprar/.
   La primera visita GET devuelve 405 porque este endpoint acepta POST; esto
   no indica un fallo del despliegue. El formulario de DRF debe estar visible.
5. Elegir Raw data, application/json y enviar:

```json
{
  "libro_id": 1,
  "direccion_envio": "Medellin - Juan Manuel Ramirez",
  "cantidad": 1
}
```

6. Comprobar HTTP 201 Created y total 178.50.
7. Abrir http://localhost:8000/inventario/ para comprobar la reduccion del stock.

Comprobaciones adicionales:
```powershell
docker compose exec web python manage.py check
docker compose exec web python manage.py test tienda_app
docker compose exec web cat /app/logs/pagos_locales_JUAN_MANUEL_RAMIREZ.log
```

Para detener conservando datos: `docker compose down`.
No agregar `-v` si se quieren conservar los volumenes y las compras.

## Paso 4.1 - AWS Academy e instancia

Este paso requiere tu acceso al Learner Lab. No se han creado recursos AWS.

1. Entrar a https://www.awsacademy.com/ con tu cuenta de estudiante.
2. Abrir LMS y el curso actual que te haya asignado el profesor.
3. Modules > Launch AWS Academy Learner Lab > Start Lab.
4. Esperar a que el indicador AWS este verde y abrir la consola AWS.
5. EC2 > Launch instance.
6. Nombre: Servidor-Django. AMI: Amazon Linux 2023, arquitectura x86_64.
7. Tipo: t2.micro, como indica el PDF, si esta disponible y permitido en tu lab.
8. Key pair: vockey si esta disponible, siguiendo el PDF principal.
9. Usar la region y red del laboratorio. Habilitar el acceso SSH requerido para
   la conexion seleccionada. El PDF principal tambien indica HTTP y HTTPS.
10. Lanzar la instancia, esperar a que este Running y copiar su IPv4 publica.
11. Instances > seleccionar instancia > Connect > EC2 Instance Connect.
    Para Amazon Linux el usuario es ec2-user. Si la conexion falla, revisar las
    reglas SSH de la instancia y las condiciones de Instance Connect de la region.

El numero de curso 116841/TEIS-2025-1 del segundo PDF es una referencia historica:
no reemplaza el curso actual de tu cuenta.

## Paso 4.2 - Git, Docker y Compose

En EC2 Instance Connect:

```bash
sudo dnf update -y
sudo dnf install -y git docker curl unzip
sudo systemctl enable --now docker
sudo usermod -a -G docker ec2-user
exit
```

Volver a conectar para que el grupo docker se aplique. Luego:
```bash
docker info
mkdir -p "$HOME/.docker/cli-plugins"
curl -fL https://github.com/docker/compose/releases/download/v2.39.4/docker-compose-linux-x86_64 -o "$HOME/.docker/cli-plugins/docker-compose"
curl -fL https://github.com/docker/compose/releases/download/v2.39.4/docker-compose-linux-x86_64.sha256 -o "$HOME/.docker/cli-plugins/docker-compose-linux-x86_64.sha256"
(cd "$HOME/.docker/cli-plugins" && expected=$(awk '{print $1}' docker-compose-linux-x86_64.sha256) && actual=$(sha256sum docker-compose | awk '{print $1}') && test "$expected" = "$actual")
chmod +x "$HOME/.docker/cli-plugins/docker-compose"
docker compose version
```

Estos comandos son para la AMI x86_64 indicada. Para ARM debe usarse el binario
aarch64; scripts/instalar_docker_ec2.sh detecta ambas arquitecturas y valida SHA256.
Si el proyecto ya esta en la instancia, tambien se puede ejecutar ese script
con `bash scripts/instalar_docker_ec2.sh` y volver a conectar al terminar.

## Paso 4.3 - Llevar el codigo a EC2

Opcion A: tu propio repositorio Git que contenga este proyecto preparado:
```bash
git clone https://github.com/TU-USUARIO/TU-REPOSITORIO.git
cd TU-REPOSITORIO
```

Sustituir la URL por la de tu repositorio. El repositorio base del profesor no
contiene automaticamente estos cambios. No subir .env a GitHub.

Opcion B: transferir el ZIP desde Windows, si tienes la clave vockey.pem y el
acceso SSH configurado. En PowerShell, desde la carpeta donde descargaste el ZIP:
```powershell
scp -i "$env:USERPROFILE\Downloads\vockey.pem" .\Proyecto_Tutorial04_PREPARADO_JUAN_MANUEL_RAMIREZ.zip ec2-user@IP-PUBLICA:/home/ec2-user/
```

Sustituir IP-PUBLICA y la ruta de la clave por los valores reales. La clave privada
se usa en tu equipo; no es necesario compartirla por el chat.

En la terminal EC2:
```bash
unzip Proyecto_Tutorial04_PREPARADO_JUAN_MANUEL_RAMIREZ.zip
cd Tutorial04_JUAN_MANUEL_RAMIREZ
python3 scripts/crear_env.py
nano .env
```

En .env, cambiar exclusivamente DJANGO_ALLOWED_HOSTS a:
```
DJANGO_ALLOWED_HOSTS=IP-PUBLICA,localhost,127.0.0.1
```

Sustituir IP-PUBLICA por la IPv4 real, sin http:// ni :8000. Mantener los secretos
generados. Guardar con Ctrl+O, Enter y salir con Ctrl+X.

Si la IP publica cambia al iniciar otra vez la instancia, actualizar esta variable
y recrear web con `docker compose up -d --force-recreate web`.

## Paso 4.4 - Arranque

```bash
bash scripts/desplegar_ec2.sh
docker compose logs web
docker compose ps
```

El script valida la configuracion y ejecuta `docker compose up -d --build`.
Esperar a que terminen las migraciones y aparezca el arranque del servidor.

La base PostgreSQL del contenedor es nueva. El seed crea los tres libros con
stock 10; no se copia la base SQLite de los tutoriales anteriores a PostgreSQL.
No se necesita crear RDS para la ruta principal de este PDF.

## Paso 4.5 - Security Group

EC2 > Instances > seleccionar instancia > Security > Security Group > Edit inbound
rules. Agregar Custom TCP, puerto 8000, origen 0.0.0.0/0, como indica el PDF.
Guardar. Conservar el acceso SSH que requiere tu modo de conexion.
No abrir el puerto de PostgreSQL: en esta ruta esta dentro de Compose.

## Paso 5 - Captura obligatoria desde AWS

1. En tu navegador abrir `http://IP-PUBLICA:8000/api/v1/comprar/`.
2. En DRF, Raw data > application/json; enviar el JSON del paso local con POST.
3. Comprobar HTTP 201 Created y la respuesta de exito.
4. Tomar una captura que incluya la barra de direcciones con la IP publica,
   el endpoint y la respuesta. Puede tomarse con Win+Shift+S.
5. Guardarla como `Captura_AWS_JUAN_MANUEL_RAMIREZ.png` y subirla a la actividad
   indicada por tu profesor. El PDF principal no da el nombre de la asignacion.

Una captura de localhost, una IP inventada o una pagina sin desplegar no cumple
la evidencia requerida. Esta captura queda pendiente hasta disponer de tu lab.

## Revision y estado real

Verificado en el entorno de trabajo del asistente:
- 37 pruebas de aplicacion aprobadas con SQLite local.
- Django check sin problemas y ninguna migracion pendiente.
- Docker Compose v2.39.4: config --quiet correcto; binario con SHA256 verificado.
- YAML, sintaxis Python y sintaxis de los scripts shell correctos.
- Generacion de .env y rechazo de sobrescritura comprobados.
- DEBUG=0: interfaz DRF respondio al GET con 405 esperado y su CSS con HTTP 200.

Pendiente:
- Construir la imagen y ejecutar el stack con un motor Docker.
- Probar la compra sobre PostgreSQL del contenedor.
- Crear/configurar EC2 en tu cuenta, desplegar y capturar la API por su IP publica.

No se presenta la validacion de Compose como prueba de ejecucion de contenedores.
No hay un motor Docker disponible ni una cuenta AWS conectada en este entorno.

## Finalizar el laboratorio

Tomar primero la captura y guardar los archivos. Detener los contenedores con
`docker compose stop` cuando termines. El segundo PDF pide borrar su RDS y detener
el contenedor al finalizar; si llegas a crear RDS en esa ruta, completar su limpieza
segun las indicaciones del profesor. Cerrar o detener el Learner Lab cuando
termine la practica. No borrar datos que aun necesites conservar.

## Fuentes oficiales consultadas

- [Instalacion de Docker en Amazon Linux 2023](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-container-image.html)
- [Instalacion del plugin Compose](https://docs.docker.com/compose/install/linux/)
- [Orden de arranque y healthchecks](https://docs.docker.com/compose/how-tos/startup-order/)
- [Acceso a RDS con security groups](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.RDSSecurityGroups.html)
