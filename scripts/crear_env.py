"""Genera secretos locales una sola vez; nunca los muestra en consola."""
from pathlib import Path
import secrets
import sys

root = Path(__file__).resolve().parent.parent
target = root / ".env"
if target.exists():
    sys.exit(".env ya existe; no se sobrescribio.")
text = (root / ".env.example").read_text(encoding="utf-8")
text = text.replace("DB_PASSWORD=\n", "DB_PASSWORD=" + secrets.token_hex(24) + "\n")
text = text.replace("DJANGO_SECRET_KEY=\n", "DJANGO_SECRET_KEY=" + secrets.token_hex(32) + "\n")
with target.open("x", encoding="utf-8", newline="\n") as stream:
    stream.write(text)
target.chmod(0o600)
print(".env creado. Ajuste DJANGO_ALLOWED_HOSTS para la IP publica de EC2.")
