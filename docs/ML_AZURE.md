# Despliegue de Predicciones ML en Azure

Este documento resume cómo preparar, entrenar y operar el modelo de predicción de reportes cuando el backend corre en **Azure App Service**.

---

## 1. Preparar datos y artefactos

1. **Usar datos reales del entorno productivo.**  
   - Conéctate a la misma base Azure PostgreSQL (variables `DB_*` ya configuradas).  
   - Ejecuta localmente:
     ```bash
     cd backend
     source venv/bin/activate
     export DB_HOST=... # si no lo tenías
     python manage.py train_prediction_model --min-samples 30
     ```
2. **Persistir el modelo**  
   - El comando genera `backend/reportes/ml/artifacts/report_resolution_model.joblib`.  
   - Inclúyelo en el commit o súbelo manualmente antes del despliegue (el workflow empaqueta todo `backend/`).  
   - Si prefieres no commitearlo, puedes copiarlo a Azure con `az webapp ssh` y dejarlo en `/home/site/wwwroot/reportes/ml/artifacts/`.

---

## 2. Configurar App Service

En el portal de Azure → App Service → *Configuration* → *Application Settings* agrega:

| Variable | Valor sugerido | Descripción |
| --- | --- | --- |
| `ENABLE_LOCAL_PREDICTIONS` | `1` | Activa el bloque `prediction` en las respuestas del backend. |
| `TRAIN_PREDICTIONS_ON_START` | `1` (opcional) | Si existe un dataset suficiente en la base, ejecuta `train_prediction_model` cada vez que se reinicia la app. |
| `TRAIN_PREDICTIONS_MIN_SAMPLES` | `30` (opcional) | Se pasa al comando anterior. Ajusta según el volumen de datos. |
| `DB_*` | (ya existentes) | Credenciales de la base PostgreSQL. |

> **Nota:** Si decides no guardar el artefacto en git, activa `TRAIN_PREDICTIONS_ON_START=1` para que la app lo genere automáticamente con los datos del servidor.

---

## 3. Pipeline de despliegue (`deploy-backend.yml`)

No necesitas cambios mayores. El ZIP generado ya contiene:

- Código Django (`backend/**`)
- Directorio `reportes/ml/artifacts/*`
- `startup.sh` (Azure lo ejecuta automáticamente si lo defines como *Startup Command*).

Sólo asegúrate de que el App Service tenga configurado el *Startup Command* apuntando a `./startup.sh`.

---

## 4. Validar en producción

1. Después del despliegue, revisa los logs:
   ```bash
   az webapp log tail --name <tu-app> --resource-group <rg>
   ```
   Deberías ver mensajes como:
   ```
   ✅ Predicciones habilitadas (ENABLE_LOCAL_PREDICTIONS=1)
   Entrenando modelo local antes de iniciar...
   ```
2. Llama al backend para verificar que venga el bloque `prediction`:
   ```bash
   curl https://<tu-backend>.azurewebsites.net/api/reportes/ | jq '.[0].prediction'
   ```
3. Abre la Static Web App (frontend) y valida la pestaña “📊 Estadísticas”.

---

## 5. Operación continua

- **Reentrenamiento manual:**  
  Cuando quieras mejorar el modelo, repite el proceso local o ejecuta:
  ```bash
  az webapp ssh --name <tu-app> --resource-group <rg>
  # dentro de la sesión
  cd /home/site/wwwroot
  source antenv/bin/activate
  python manage.py train_prediction_model --min-samples 30
  ```

- **Monitoreo:**  
  Usa Azure Monitor/Application Insights para revisar el desempeño de la app y crear alertas si el entrenamiento falla.

- **Backups del modelo:**  
  Copia el archivo `.joblib` a Blob Storage o a un repositorio privado para mantener versiones previas.

---

## 6. Próximos pasos (ML Ops avanzado)

Cuando necesites más formalidad:

1. Usa Azure Machine Learning para manejar datasets, experimentos y versionado de modelos.
2. Publica las predicciones como un endpoint dedicado (Managed Online Endpoint) o genera batch scoring que el backend consuma.
3. Habilita monitoreo de drift y pipelines automatizados de reentrenamiento.
4. Si migras a AWS, puedes replicar este esquema con SageMaker + S3 + Glue sin cambios en el frontend/backend.

---

Con esta configuración tienes un flujo reproducible y fácil de operar: entrenas donde prefieras, subes el modelo y Azure se encarga de servirlo con el backend actual. Cuando quieras subir de nivel (Azure ML/SageMaker), sólo reemplazas la pieza que genera las predicciones.***

