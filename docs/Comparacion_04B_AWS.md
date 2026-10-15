# Comparacion de los dos PDFs y ruta RDS

## Como encajan

| Aspecto | tutorial04_Docker_AWS.pdf | tutorial04-B-AWS.pdf |
|---|---|---|
| Encabezado | Tutorial 04 | Tutorial 05, tarea en Teams |
| Aplicacion | Tienda API del tutorial 03 | Texto menciona Laravel; enlaza djangoDocker |
| Base de datos | PostgreSQL 15 en Compose | RDS MySQL 8.0 |
| Clave EC2 | vockey | Sin key pair |
| URL | IP:8000/api/v1/comprar/ | IP/public/ |
| Evidencia | Captura de respuesta JSON desde AWS | Ver proyecto desplegado y completar Teams |

Se preparo la ruta principal para Tienda API. El PDF B se usa como apoyo visual
para abrir Academy, iniciar Learner Lab, crear EC2 y conectarse por Instance
Connect. No se puede copiar su receta de Laravel a Tienda API sin adaptar el codigo.

## Comprobacion del repositorio citado por B

Se inspecciono https://github.com/Nram94/djangoDocker:
- Es otro proyecto Django, con Python 3.8/Django 4.1 en sus archivos actuales.
- Su Dockerfile expone 8000 y no define CMD/ENTRYPOINT.
- Su Compose si define runserver 0.0.0.0:8000 y publica 8000:8000.
- La configuracion examinada no lee la plantilla .env para configurar la BD.

Por tanto, `docker run -p 80:80 django-app` no garantiza arrancar esa aplicacion,
y `/public/` es una referencia de Laravel que no corresponde al endpoint de
Tienda API. Estas diferencias se encontraron al revisar el codigo, no se infirio
que hubiera un despliegue AWS funcional.

## Si el profesor exige tambien la ruta RDS MySQL del PDF B

Esto requiere confirmar si desea ese segundo laboratorio independiente o una
adaptacion de Tienda API. El proyecto entregado sigue PostgreSQL; una base RDS
MySQL no funciona con django.db.backends.postgresql y psycopg2-binary.

Pasos de infraestructura del PDF B:

1. Iniciar el Learner Lab del curso actual y crear EC2 Amazon Linux 2023.
2. Instalar/activar Docker e instalar Git, como explica la guia principal.
3. RDS > Create database > MySQL, version 8.0 si esta disponible en el lab.
   Usar el identificador y el usuario que indique el profesor, y una contrasena
   propia. La disponibilidad de la opcion Free tier depende de tu consola y cuenta;
   no se afirma que una cuenta Academy tenga una cuota gratis ilimitada.
4. Colocar EC2 y RDS en una red con conectividad entre ambos. En el security group
   de RDS, permitir TCP 3306 desde el security group de EC2, para el trafico EC2-RDS.
   No es necesario abrir la base de datos a todo Internet.
5. En EC2, instalar el cliente indicado para Amazon Linux:
   `sudo dnf install -y mariadb105`.
6. Copiar el endpoint de RDS y ejecutar, sustituyendo el endpoint real:
   `mysql -h ENDPOINT-RDS -P 3306 -u admin -p`.
   Introducir la contrasena en el prompt. Crear `djangodocker` con
   `CREATE DATABASE djangodocker;` y salir con `exit`.
7. Si se usa el repositorio djangoDocker, adaptar su settings para leer el entorno,
   conservar un driver compatible de MySQL, y definir un comando de arranque.
   No basta con copiar .env si settings no lo lee.
8. Publicar el puerto realmente usado por Django, aplicar migraciones con esa
   base y abrir la ruta definida por ese proyecto. Para Tienda API, la ruta requerida
   por el PDF principal sigue siendo /api/v1/comprar/ en el puerto 8000.
9. Guardar la evidencia y completar la tarea de Teams que indique el profesor.
10. Eliminar RDS y detener el contenedor al terminar, como pide el PDF B, despues
    de conservar lo necesario y siguiendo el procedimiento de la cuenta Academy.

Estado: no se ha creado RDS ni ejecutado ese proyecto alternativo. Estas son
instrucciones para completar esa ruta con acceso real al laboratorio, no evidencia
de que se haya desplegado.

Como alternativa si el objetivo fuera usar Tienda API con RDS manteniendo el motor,
se podria usar RDS PostgreSQL y DB_HOST apuntando a su endpoint, con una receta
Compose sin el servicio db local. Esto requiere acordarlo con el profesor porque
cambia la eleccion MySQL especificada en B.
