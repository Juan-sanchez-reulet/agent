# Monitor de Citas — Embajada de EEUU en Madrid

Este script revisa automáticamente cada 5 minutos si hay citas disponibles antes del 17 de septiembre y te manda una notificación al móvil + un email en cuanto aparezca un hueco.

---

## Lo que necesitas antes de empezar

- Tu cuenta de [ais.usvisa-info.com](https://ais.usvisa-info.com/en-es/niv) (el email y contraseña con los que reservas la cita)
- Una cuenta de Gmail
- La app **ntfy** instalada en tu móvil

---

## Instalación (5 minutos)

### 1. Descarga el proyecto

Abre el Terminal (`Cmd + Espacio`) y pega esto:

```bash
cd ~/Desktop && git clone https://github.com/Juan-sanchez-reulet/agent.git visa-monitor && cd visa-monitor
```

> Si no tienes git instalado, te pedirá instalarlo — acepta.

### 2. Instala las dependencias

```bash
pip install -r requirements.txt
```

### 3. Crea tu archivo de configuración

```bash
cp .env.example .env
open -e .env
```

Se abrirá un archivo de texto. Rellena cada línea con tus datos:

```
VISA_EMAIL=          ← tu email de ais.usvisa-info.com
VISA_PASSWORD=       ← tu contraseña de ais.usvisa-info.com
GMAIL_APP_PASSWORD=  ← ver paso 4
NOTIFY_EMAIL=        ← el email donde quieres recibir las alertas
TARGET_DATE=2026-09-16
APPOINTMENT_URL=https://ais.usvisa-info.com/en-es/niv/schedule/TU_ID/appointment?confirmed_limit_message=1&commit=Continue
NTFY_TOPIC=         ← un nombre único cualquiera, ej: visa-madrid-maria-2026
```

> **¿Cuál es tu APPOINTMENT_URL?** Entra en ais.usvisa-info.com, inicia sesión, ve a "Schedule Appointment" y copia la URL de la barra del navegador.

Guarda el archivo (`Cmd + S`) y ciérralo.

### 4. Genera tu contraseña de Gmail para la app

1. Ve a [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) con tu cuenta de Gmail
   > Si no te aparece esta opción, primero activa la verificación en dos pasos en [myaccount.google.com/security](https://myaccount.google.com/security)
2. Pon cualquier nombre (ej. "visa-monitor") y haz clic en **Crear**
3. Copia las 16 letras que aparecen y pégalas en el `.env` donde pone `GMAIL_APP_PASSWORD=`

### 5. Configura la app ntfy en el móvil

1. Abre la app ntfy
2. Toca el **+** y suscríbete al topic que pusiste en `NTFY_TOPIC=` (ej. `visa-madrid-maria-2026`)
3. Para que suene aunque el móvil esté en silencio:
   - **iOS:** Ajustes → Ntfy → Notificaciones → activa **"Notificaciones de tiempo crítico"**
   - **Android:** mantén pulsada la notificación de ntfy → activar sonido de alarma

---

## Prueba que todo funciona

Pega esto en el Terminal:

```bash
TARGET_DATE=2026-12-31 python3 monitor.py
```

Deberías ver algo así:
```
[ALERT] Push notification sent to ntfy topic: visa-madrid-maria-2026
[ALERT] Email sent — available dates: 2026-09-28, 2026-10-01, ...
```

Y en tu móvil llegará una notificación y en tu email una alerta. Si ves eso, **todo está funcionando**.

---

## Activa el monitor 24/7

Para que corra solo en segundo plano sin que tengas que hacer nada:

```bash
cp com.visa.monitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.visa.monitor.plist
```

Para comprobar que está activo:

```bash
launchctl list | grep visa
```

Si ves `com.visa.monitor` en el resultado, está corriendo. Puedes cerrar el Terminal.

---

## ¿Cómo sé que sigue funcionando?

Puedes ver el historial de chequeos en cualquier momento:

```bash
tail -50 ~/Library/Logs/visa-monitor.log
```

Verás una línea cada 5 minutos. Mientras aparezcan líneas nuevas, el monitor está activo.

---

## Pararlo cuando ya no lo necesites

```bash
launchctl unload ~/Library/LaunchAgents/com.visa.monitor.plist
```

---

## Algo no funciona

| Error | Solución |
|---|---|
| `AUTH ERROR` | Revisa tu email y contraseña de usvisa en el `.env` |
| `NOTIFY ERROR: BadCredentials` | El `GMAIL_APP_PASSWORD` no es correcto, genera uno nuevo |
| `No slots available` | Normal — significa que no hay huecos aún, sigue esperando |
| Push no llega al móvil | Comprueba que el topic en la app ntfy coincide exactamente con el del `.env` |
