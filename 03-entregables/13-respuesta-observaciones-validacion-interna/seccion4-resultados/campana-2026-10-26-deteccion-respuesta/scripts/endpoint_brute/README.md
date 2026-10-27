# Endpoint de prueba para fuerza bruta HTTP (servicio aislado de laboratorio)

**Problema corregido.** La receta anterior combinaba `auth_basic` con `return 200` en el mismo bloque nginx. En
nginx `return` se ejecuta en la fase *rewrite*, **antes** de la fase *access* (`auth_basic`), así que respondía 200
**sin comprobar la autenticación**: nunca habría 401 y la fuerza bruta no se detectaría.

Se entrega una implementación correcta y **probada en aislamiento** (no en srv-dmz todavía).

## Comportamiento correcto (verificado el 27-oct en loopback)

| Petición | Código |
|---|---|
| sin credenciales | **401** (con `WWW-Authenticate`) |
| credenciales inválidas (`fake:...`) | **401** |
| credencial de control válida | **200** |
| ruta equivocada | 404 |

Cada petición se registra: `fecha cliente método ruta user=<usuario> -> <código>`. Un 401 es fallo de auth; un
404/000 **no** lo es (no confundir).

## Opción A — Python stdlib (preferida: sin ambigüedad de fases)

`app.py` (en esta carpeta). Servicio aislado, sin dependencias.

```bash
# [srv-dmz adminsrvdmz] -> lo ejecutas tú (NOPASSWD ALL disponible)
sudo install -d -o adminsrvdmz -g adminsrvdmz /opt/brute-lab
sudo install -m 0644 app.py /opt/brute-lab/app.py
# unidad systemd (abajo). Puerto y credencial de control por entorno.
sudo cp ppi-brute-lab.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl start ppi-brute-lab
```

Dependencias: solo `python3` (ya presente en srv-dmz). Permisos: corre como `adminsrvdmz`, escucha en el puerto de
laboratorio (18081 por defecto), escribe su log en `/opt/brute-lab/brute.log`.

## Opción B — nginx (si se prefiere nginx), **corregida**

El 200 debe quedar **detrás** de la fase de autenticación. No usar `return` en el mismo bloque.

```nginx
server {
    listen 18081;
    access_log /var/log/nginx/brute-lab.access.log;
    location /auth {
        auth_basic "lab";
        auth_basic_user_file /etc/nginx/.htpasswd-lab;
        root /var/www/brute-lab;          # sirve un fichero real -> 200 TRAS la auth
        try_files /ok.txt =404;
    }
}
```

```bash
sudo htpasswd -bc /etc/nginx/.htpasswd-lab control control123   # credencial de control (200)
sudo install -d /var/www/brute-lab && echo ok | sudo tee /var/www/brute-lab/ok.txt
sudo cp brute-lab.conf /etc/nginx/conf.d/ && sudo nginx -t && sudo systemctl reload nginx
```

Verificación (una sola petición por caso, benigna):
```bash
curl -s -o /dev/null -w "%{http_code}\n" --max-time 3 http://10.10.30.10:18081/auth                 # 401
curl -s -o /dev/null -w "%{http_code}\n" --max-time 3 -u fake:fake http://10.10.30.10:18081/auth     # 401
curl -s -o /dev/null -w "%{http_code}\n" --max-time 3 -u control:control123 http://10.10.30.10:18081/auth  # 200
```

## Copia del estado anterior y retirada

```bash
# antes: anotar que el puerto 18081 estaba cerrado (verificado 26-oct) y que no había servicio
# retirada (tras campaña B):
sudo systemctl stop ppi-brute-lab && sudo rm /etc/systemd/system/ppi-brute-lab.service && sudo systemctl daemon-reload
sudo rm -rf /opt/brute-lab
# opción nginx:
sudo rm /etc/nginx/conf.d/brute-lab.conf /etc/nginx/.htpasswd-lab; sudo rm -rf /var/www/brute-lab; sudo systemctl reload nginx
```

## Que el detector observe el 401 (no basta con que el servidor lo devuelva)

Obtener un 401 en srv-dmz **no garantiza** que CyberFlow lo vea. Hay que comprobar:

1. **El tráfico cruza el espejo SPAN** que llega al sensor (ens37). El puerto 18081 debe estar en el troncal
   espejado igual que el 80/443; si el cortafuegos o el espejo filtran ese puerto, el sensor no lo ve.
2. **Suricata reconoce HTTP en 18081.** Por defecto Suricata detecta HTTP por patrón, pero su `app-layer` y los
   puertos HTTP configurados (`HTTP_PORTS`) influyen en el parseo. Comprobar en el sensor:
   `suricata --dump-config | grep -i 'http.*port'` y, tras una petición de prueba, que aparezcan eventos
   `event_type:http` con `status:401` en `eve.json` para 10.10.30.10:18081.
3. **El extractor toma esos eventos.** `http_request_count_60s`, `http_auth_failure_ratio_60s` se construyen de
   `load_app_observations(eve)`. Verificar que `http_auth_failure_ratio_60s` sube con los 401 en la ventana de la Kali.

Si 18081 no se parsea como HTTP, usar un puerto ya reconocido (p.ej. 80 con una ruta `/auth`) o añadir 18081 a
`HTTP_PORTS` de Suricata (cambio de infraestructura, documentarlo). **Pendiente de comprobar en srv-dmz.**
