param(
    [Parameter(Mandatory = $true)]
    [string]$PublicIp
)
$ErrorActionPreference = "Stop"
$parsedIp = [System.Net.IPAddress]::Parse($PublicIp)
if ($parsedIp.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
    throw "Indique la IPv4 publica de su instancia EC2."
}
Write-Host "Tutorial 05 - Juan Manuel Ramirez"
Write-Host "IP de EC2: $PublicIp | Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Comprobando primero que Nginx responde por el puerto 80..."
& curl.exe --fail --silent --show-error --max-time 10 "http://$PublicIp/health/"
if ($LASTEXITCODE -ne 0) {
    throw "El puerto 80 no responde. Verifique EC2 antes de probar aislamiento."
}
Write-Host "`nIntento directo al backend: http://${PublicIp}:8000/"
& curl.exe --verbose --connect-timeout 5 --max-time 10 "http://${PublicIp}:8000/"
$directExit = $LASTEXITCODE
if ($directExit -eq 0) {
    throw "El puerto 8000 responde: revise los contenedores y sus puertos publicados."
}
if ($directExit -eq 28) {
    Write-Host "Timeout esperado: el backend no es accesible directamente por 8000."
} elseif ($directExit -eq 7) {
    Write-Host "Conexion rechazada: el puerto no es accesible. El PDF pide timeout; cierre la regla 8000 del Security Group."
} else {
    Write-Host "curl finalizo con codigo $directExit. Revise la salida antes de usarla como evidencia."
}
Write-Host "Tome la captura de esta terminal; debe verse el intento y su resultado real."
