#!/bin/bash
set -euo pipefail
sudo dnf update -y
sudo dnf install -y git docker curl unzip
sudo systemctl enable --now docker
sudo usermod -a -G docker ec2-user
# Version fija y descarga oficial; verificar SHA256 antes de instalar.
compose_version="v2.39.4"
case "$(uname -m)" in
  x86_64) compose_arch=x86_64 ;;
  aarch64) compose_arch=aarch64 ;;
  *) echo "Arquitectura no soportada" >&2; exit 1 ;;
esac
compose_dir=$(mktemp -d)
trap 'rm -rf "$compose_dir"' EXIT
compose_file="docker-compose-linux-${compose_arch}"
compose_url="https://github.com/docker/compose/releases/download/${compose_version}"
curl --fail --location "${compose_url}/${compose_file}" -o "${compose_dir}/${compose_file}"
curl --fail --location "${compose_url}/${compose_file}.sha256" -o "${compose_dir}/${compose_file}.sha256"
(cd "$compose_dir" && sha256sum -c "${compose_file}.sha256")
sudo install -D -m 0755 "${compose_dir}/${compose_file}" /usr/local/lib/docker/cli-plugins/docker-compose
echo "Instalacion completada. Cierre y vuelva a conectar la terminal EC2."
