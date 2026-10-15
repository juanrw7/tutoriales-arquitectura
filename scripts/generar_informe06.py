"""Genera borrador o informe PDF a partir de capturas y logs suministrados."""
import argparse
import ipaddress
from pathlib import Path
import re
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

parser=argparse.ArgumentParser()
parser.add_argument('--draft',action='store_true')
parser.add_argument('--ip')
parser.add_argument('--v1',type=Path)
parser.add_argument('--v2',type=Path)
parser.add_argument('--logs',type=Path)
parser.add_argument('--output',type=Path,required=True)
a=parser.parse_args()
if a.output.exists():parser.error('El archivo de salida ya existe; use otro nombre para conservarlo.')
if not a.draft:
    if not all([a.ip,a.v1,a.v2,a.logs]):parser.error('Se requieren --ip, --v1, --v2 y --logs para el informe final.')
    try: ip=ipaddress.ip_address(a.ip)
    except ValueError:parser.error('La IP debe ser una direccion valida.')
    if ip.version!=4 or not ip.is_global:parser.error('Se requiere la IPv4 publica de EC2.')
    for path in [a.v1,a.v2,a.logs]:
        if not path.is_file():parser.error('Archivo no encontrado: '+str(path))
    try:
        ImageReader(str(a.v1)).getSize();ImageReader(str(a.v2)).getSize()
    except Exception:parser.error('Las capturas deben ser imagenes validas.')
    logs=a.logs.read_text(encoding='utf-8-sig',errors='replace')
    lines=logs.splitlines()
    valid_v1=any('GET /api/v1/productos/' in x and 'upstream=django_v1' in x and ':8000' in x for x in lines)
    valid_v2=any('POST /api/v2/comprar' in x and 'upstream=flask_v2' in x and ':5000' in x for x in lines)
    if not valid_v1 or not valid_v2:parser.error('Los logs deben mostrar GET v1 -> Django:8000 y POST v2 -> Flask:5000. No usar los logs de prueba local.')
fontroot=Path(__file__).parent/'fonts'
for name,file in [('Normal','DejaVuSans.ttf'),('Negrita','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(fontroot/file)))
a.output.parent.mkdir(parents=True,exist_ok=True)
c=canvas.Canvas(str(a.output),pagesize=landscape(A4));W,H=landscape(A4);page=0
c.setAuthor('Juan Manuel Ramirez');c.setTitle('Tutorial 06 - Strangler Pattern')
def heading(title,subtitle):
    global page
    page+=1;c.setFillColor(HexColor('#172033'));c.setFont('Negrita',18);c.drawString(36,H-40,title)
    c.setFont('Normal',10);c.drawString(36,H-61,subtitle)
    c.drawString(36,H-79,'Juan Manuel Ramirez | Arquitectura de Software | Tutorial 06')
    c.setFont('Negrita',9)
    if a.draft:
        c.setFillColor(HexColor('#9a3412'));c.drawString(36,H-99,'BORRADOR - PENDIENTE EJECUCION Y EVIDENCIAS REALES DE AWS')
    else:
        c.setFillColor(HexColor('#172033'));c.drawString(36,H-99,'Instancia EC2: '+a.ip)
    c.setStrokeColor(HexColor('#cbd5e1'));c.line(36,H-111,W-36,H-111)
    c.setFont('Normal',8);c.setFillColor(HexColor('#475569'));c.drawString(36,22,'Tutorial 06 - Coexistencia v1/v2 y enrutamiento por Nginx');c.drawRightString(W-36,22,str(page))
def screenshot(title,subtitle,path,notes):
    heading(title,subtitle)
    c.setFillColor(HexColor('#172033'));c.setFont('Normal',9);c.drawString(36,H-130,notes)
    left,bottom,width,height=36,53,W-72,H-205
    if a.draft:
        c.setFillColor(HexColor('#f8fafc'));c.setStrokeColor(HexColor('#cbd5e1'));c.rect(left,bottom,width,height,fill=1)
        c.setFillColor(HexColor('#172033'));c.setFont('Negrita',15)
        c.drawCentredString(W/2,bottom+height/2+16,'PENDIENTE: CAPTURA REAL DE POSTMAN EN AWS')
        c.setFont('Normal',10);c.drawCentredString(W/2,bottom+height/2-9,'La imagen debe mostrar la IP publica, el metodo, la URL y la respuesta.')
        c.drawCentredString(W/2,bottom+height/2-31,'Esta plantilla no es la evidencia final para entregar.')
    else:
        im=ImageReader(str(path));iw,ih=im.getSize();scale=min(width/iw,height/ih)
        c.drawImage(im,left+(width-iw*scale)/2,bottom+(height-ih*scale)/2,iw*scale,ih*scale)
    c.showPage()
ip=a.ip if not a.draft else 'IP-AWS'
screenshot('1. Prueba de coexistencia - Django v1','GET http://'+ip+'/api/v1/productos/',a.v1,'Respuesta esperada: HTTP 200 con productos serializados por el monolito Django.')
screenshot('2. Prueba de estrangulamiento - Flask v2','POST http://'+ip+'/api/v2/comprar',a.v2,'Respuesta esperada: HTTP 200 y mensaje de compra procesada por el Microservicio Flask.')
if a.draft:
    heading('3. Logs de orquestacion - Nginx','Salida real de: docker compose logs --no-color nginx')
    c.setFillColor(HexColor('#f8fafc'));c.setStrokeColor(HexColor('#cbd5e1'));c.rect(36,53,W-72,H-205,fill=1)
    c.setFillColor(HexColor('#172033'));c.setFont('Negrita',15);c.drawCentredString(W/2,H/2,'PENDIENTE: LOGS DE LOS DOS BACKENDS EN AWS')
    c.setFont('Normal',10);c.drawCentredString(W/2,H/2-27,'Deben aparecer upstream=django_v1 (:8000) y upstream=flask_v2 (:5000).')
    c.drawCentredString(W/2,H/2-49,'No se incluyen registros ficticios ni logs locales como si fueran de AWS.')
    c.showPage()
else:
    wrapped=[]
    for line in lines:
        wrapped.extend(textwrap.wrap(line,width=151,replace_whitespace=False,drop_whitespace=False) or [''])
    for index in range(0,len(wrapped),42):
        heading('3. Logs de orquestacion - Nginx','Salida de docker compose logs --no-color nginx | Parte '+str(index//42+1))
        c.setFillColor(HexColor('#172033'));c.setFont('Mono',7.5);y=H-136
        for line in wrapped[index:index+42]:
            c.drawString(36,y,line);y-=9.4
        c.showPage()
c.save()
print('PDF generado: '+str(a.output))
