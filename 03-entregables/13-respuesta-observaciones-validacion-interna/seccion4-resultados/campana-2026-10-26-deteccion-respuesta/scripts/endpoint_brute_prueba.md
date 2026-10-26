# Endpoint de prueba para fuerza bruta HTTP (preparación reproducible)

Hoy no existe: `/login` → 404 y 8081 cerrado. La fuerza bruta necesita un endpoint que devuelva **401** ante
credenciales inválidas (no 404 ni error de conexión). Se despliega como **servicio aislado de laboratorio** en srv-dmz
y se detiene al terminar la campaña B.

**Quién:** `[srv-dmz adminsrvdmz] → lo ejecutas tú` (requiere abrir un puerto de laboratorio y, si procede, una regla
en el cortafuegos para que la Kila alcance ese puerto).

## Opción mínima: nginx con Basic Auth

```bash
# en srv-dmz, puerto de laboratorio (p.ej. 8081)
sudo htpasswd -bc /etc/nginx/.htpasswd-lab usuario_valido clave_valida   # un login legítimo de control
cat >/etc/nginx/conf.d/brute-lab.conf <<'CONF'
server {
    listen 8081;
    location /auth {
        auth_basic "lab";
        auth_basic_user_file /etc/nginx/.htpasswd-lab;
        return 200 "ok\n";
    }
}
CONF
sudo nginx -t && sudo systemctl reload nginx
```

- Credenciales inválidas → **401** (fuerza bruta). El usuario de control válido → 200.
- Registra `access.log` con el código por petición: evidencia de actividad y de 401.

## Verificación previa (benigna)

```bash
# [bastión gadmin] o [Kali] -> una sola petición, sin bucle
curl -s -o /dev/null -w "%{http_code}\n" --max-time 3 -u fake:fake http://10.10.30.10:8081/auth   # debe dar 401
curl -s -o /dev/null -w "%{http_code}\n" --max-time 3 -u usuario_valido:clave_valida http://10.10.30.10:8081/auth  # 200
```

Registrar el `BRUTE_PUERTO` (8081) y `BRUTE_RUTA` (/auth) en el entorno de `generar_campana.py` y en `escenarios.json`.

## Limpieza (tras campaña B)

```bash
sudo rm /etc/nginx/conf.d/brute-lab.conf /etc/nginx/.htpasswd-lab
sudo systemctl reload nginx
```
