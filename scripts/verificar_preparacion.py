"""Valida archivos del despliegue; no ejecuta contenedores ni crea recursos AWS."""
from pathlib import Path
import ast
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import yaml

root=Path(__file__).resolve().parent.parent
compose=yaml.safe_load((root/'docker-compose.yml').read_text())
assert compose['services']['db']['image']=='postgres:15'
web=compose['services']['web_django']
assert web['depends_on']['db']['condition']=='service_healthy'
assert web['environment']['DB_HOST']=='db'
assert 'ports' not in web
assert web['expose']==['8000']
assert web['command'][0]=='gunicorn'
assert web['command'][1]=='Tienda.wsgi:application'
nginx=compose['services']['nginx']
assert nginx['ports']==['80:80']
assert nginx['depends_on']['web_django']['condition']=='service_healthy'
assert nginx['depends_on']['pagos_flask']['condition']=='service_healthy'
assert 'ports' not in compose['services']['pagos_flask']
assert compose['services']['pagos_flask']['expose']==['5000']
assert nginx['networks']==['edge']
assert compose['services']['db']['networks']==['database']
assert compose['networks']['database']['internal'] is True
conf=(root/'nginx/nginx.conf').read_text()
assert 'server web_django:8000;' in conf and 'listen 80;' in conf
assert 'proxy_pass http://django_v1;' in conf
assert 'proxy_pass http://flask_v2;' in conf
assert 'upstream=$proxy_host' in conf
assert 'ports' not in compose['services']['db']
assert 'postgres_data' in compose['volumes'] and 'payments_data' in compose['volumes']
assert web['environment']['PAYMENTS_LOG_DIR']=='/app/logs'
assert (root/'Dockerfile').exists() and 'FROM python:3.11-slim' in (root/'Dockerfile').read_text()
ignored=(root/'.dockerignore').read_text().splitlines()
assert '.env' in ignored and '*.sqlite3' in ignored and '*.log' in ignored
for file in root.rglob('*.py'):
    if '__pycache__' not in file.parts:
        ast.parse(file.read_text(encoding='utf-8'))
for file in ['entrypoint.sh','scripts/instalar_docker_ec2.sh','scripts/desplegar_ec2.sh']:
    if shutil.which('bash'):
        subprocess.run(['bash','-n',str(root/file)],check=True)
with tempfile.TemporaryDirectory() as directory:
    tmp=Path(directory); (tmp/'scripts').mkdir()
    shutil.copy2(root/'scripts/crear_env.py',tmp/'scripts/crear_env.py')
    shutil.copy2(root/'.env.example',tmp/'.env.example')
    subprocess.run([os.sys.executable,str(tmp/'scripts/crear_env.py')],check=True,stdout=subprocess.DEVNULL)
    created=(tmp/'.env').read_text()
    assert 'DB_PASSWORD=\n' not in created and 'DJANGO_SECRET_KEY=\n' not in created
    original=(tmp/'.env').read_bytes()
    second=subprocess.run([os.sys.executable,str(tmp/'scripts/crear_env.py')],capture_output=True)
    assert second.returncode!=0 and (tmp/'.env').read_bytes()==original
compose_bin=os.environ.get('COMPOSE_VALIDATOR')
if compose_bin:
    env=dict(os.environ,DB_PASSWORD=secrets.token_hex(24),DJANGO_SECRET_KEY=secrets.token_hex(32))
    subprocess.run([compose_bin,'-f',str(root/'docker-compose.yml'),'config','--quiet'],env=env,check=True)
    print('Docker Compose config: correcto (sin iniciar contenedores).')
else:
    print('YAML validado; Compose config pendiente si no hay CLI disponible.')
print('Configuracion, sintaxis, persistencia y generacion de .env: correctas.')
