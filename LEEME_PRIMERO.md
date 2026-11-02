# Pistacho QA — léeme primero

Equipo `pistacho`: Elías Ventura, Lilly Flores y Andrés Avilés.

## Resultados actuales (RoBERTa-base)

- Modelo entrenado localmente desde `FacebookAI/roberta-base`: SQuAD 2.0 completo
  (130 319 preguntas), dos épocas, 112 min en una RTX 4050 Laptop.
- Validación separada (2000 preguntas): 81,25 % EM y 83,77 % F1.
- Ejemplos públicos: 5 de 5 correctos.
- 50 solicitudes locales en CPU: 19,9 s; media 0,40 s; máxima 0,87 s.
- 30 pruebas automatizadas aprobadas.
- El modelo anterior (DistilBERT, 58,4 EM / 60,4 F1, 3 de 5) está documentado en
  `logs/distilbert-baseline/`.

## Abrir el servicio

Los pesos van en `artifacts/roberta-squad2/` (fuera de Git). En PowerShell, dentro
de esta carpeta:

```powershell
$env:QA_API_TOKEN = "<token acordado>"   # nunca en el código ni en Git
.\run.ps1
```

Verifica http://127.0.0.1:8000/health → `{"status":"ok"}`. Luego, en otra terminal:

```powershell
ngrok http 8000    # https://boil-confiding-default.ngrok-free.dev (dominio fijo)
```

Respaldo: `cloudflared tunnel --url http://127.0.0.1:8000` (la URL cambia cada vez).

## Archivos importantes

- REPORT.md: informe en inglés.
- docs/COMPLIANCE.md: auditoría de la sección V y pendientes.
- logs/: curva de pérdida, registros, validación, ejemplos públicos y pruebas.

## Pendientes

Dry run oficial por el túnel desde otra red, enviar la URL al docente, subir los
pesos nuevos como release, mover la etiqueta `submission`, y preparar pitch y Q&A.
