# Pistacho QA — versión cerrada

Equipo: Elías Ventura, Lilly Flores y Andrés Avilés.
Versión cerrada el 30 de octubre de 2026, para entrega el 31 de octubre.

## Resultados reales

- Modelo entrenado localmente desde DistilBERT base: 40 000 preguntas, dos épocas.
- 30 pruebas automatizadas aprobadas.
- Validación separada: 58,40 % EM y 60,37 % F1.
- Ejemplos públicos: 3 de 5 correctos. Los dos fallos están explicados en REPORT.md.
- 50 solicitudes locales en CPU: 12,71 s; máxima individual 0,54 s.
- Cloudflare probado: media de 0,48 s en los cinco ejemplos públicos.

## Abrir el servicio en esta computadora

La copia del Escritorio incluye el entorno Python y los pesos entrenados.
Abre PowerShell dentro de esta carpeta. Establece QA_API_TOKEN en esa terminal
con el valor acordado con el docente y ejecuta:

```powershell
.\run.ps1
```

Para verificar que cargó, abre http://127.0.0.1:8000/health. Debe responder
`{"status":"ok"}`. /info y /predict requieren el token Bearer.

Para abrir un túnel nuevo en otra terminal:

```powershell
.\tools\cloudflared-verified.exe tunnel --url http://127.0.0.1:8000 --protocol http2
```

La URL cambia en cada arranque. El túnel usado en las pruebas fue cerrado.
No hay un token de acceso real guardado en esta carpeta.

Si copias el proyecto a otra computadora, ejecuta setup.ps1 para recrear el
entorno con Python 3.12. No necesitas volver a entrenar si conservas artifacts.
No ejecutes train.ps1 salvo que quieras iniciar otro entrenamiento.

## Archivos importantes

- REPORT.md: informe completo en inglés.
- docs/COMPLIANCE.md: auditoría de la sección V y pendientes.
- docs/PRESENTATION.md: preparación del pitch y preguntas individuales.
- logs/: curvas, registros, resultados y pruebas.
- artifacts/distilbert-squad2/: modelo entrenado; fuera de Git.
- .git/: historial original y cambios en una rama aparte.

## Pendientes externos

Confirmar el token y el nombre registrado con el docente; crear/configurar una
cuenta de ngrok y probar el túnel de respaldo; hacer el ensayo oficial desde otra
red y compartir la URL; preparar el pitch y Q&A. No se afirma que estos pasos
estén hechos ni que el modelo obtendrá una nota específica.

La etiqueta Git `submission` identifica esta versión de código y evidencias.
Para ver su hash exacto: `git rev-parse submission`.
