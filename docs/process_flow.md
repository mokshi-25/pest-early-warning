# Process Flow & Methodology

## Stage 1 — Data Collection & Preprocessing
- **Source options**: PlantVillage, IP102 (insect pest dataset), or
  field-collected images from the target region's crops.
- **Labeling**: one folder per pest class under `data/train|val|test/`.
- **Preprocessing** (`src/data_preprocessing.py`):
  - Resize to 224×224 (MobileNetV2 input size)
  - Normalize pixel values to [0, 1]
  - Augment training data: flips, rotation, zoom, contrast jitter — to
    generalize across lighting/angle variation seen in field photos.

## Stage 2 — Pest Detection Model
- **Architecture**: MobileNetV2 (ImageNet-pretrained) as a frozen feature
  extractor + custom classification head (GAP → Dense(128) → Dense(num_classes,
  softmax)). Chosen for its small footprint (deployable on farmer mobile
  devices) and strong accuracy/latency tradeoff.
- **Training** (`src/model_train.py`):
  - Phase 1: train only the classification head (backbone frozen), Adam
    lr=1e-3.
  - Phase 2: unfreeze last ~30 backbone layers and fine-tune at a lower
    learning rate (1e-5) for a few epochs.
  - Early stopping + checkpointing on validation accuracy.
- **Evaluation metrics**: accuracy, macro-F1 (class imbalance is common in
  pest datasets), confusion matrix per pest class.
- **Inference** (`src/predict.py`): loads the saved model + class map, returns
  predicted pest class and confidence for a new image.

## Stage 3 — Regional Weather Ingestion
- **Source**: Open-Meteo REST API (`src/weather_api.py`) — free, no API key,
  returns current conditions + 7-day forecast (temperature, humidity,
  precipitation, wind) for any lat/long.
- Swap-in point for production: a paid provider (e.g. OpenWeatherMap,
  Tomorrow.io) if higher-resolution or hyperlocal forecasts are needed.

## Stage 4 — Risk Fusion Engine
- **Core idea**: each pest species has a known favorable climate envelope
  (temperature range, humidity range, rainfall sensitivity) derived from
  agronomy literature/extension guidance (`PEST_PROFILES` in
  `src/risk_engine.py`).
- For each of the next 7 forecast days, compute a **favorability score
  (0–1)** as a weighted blend:
  - 40% temperature fit
  - 35% humidity fit
  - 25% rainfall fit (direction depends on species — some pests are
    suppressed by heavy rain, others follow it with a lag)
- Aggregate the 7-day favorability into a single **weather risk** score,
  weighting near-term days more heavily (risk closer to "now" matters more
  for actionability).
- If an image-based detection confidence is available, blend it 50/50 with
  the weather risk — a confirmed sighting plus favorable weather is treated
  as higher-confidence than either signal alone.
- Output: **0–100 risk score** + categorical level (LOW / MODERATE / HIGH).

## Stage 5 — Early Warning & Alerting
- `src/alert_system.py` converts a risk result into a plain-language alert
  with a **recommended action** tied to the risk level (routine monitoring →
  increased monitoring → inspect + treat within 24–48h).
- Alerts are logged to `logs/alerts.log` (JSON lines) for historical
  tracking/auditing.
- Pluggable stubs for email (`send_email_alert`) and SMS (`send_sms_alert`)
  — wire in SendGrid/Twilio (or a local SMS gateway) for production delivery.
- `app.py` (Streamlit) ties every stage into one interactive dashboard: pick
  a region + pest → optionally upload a photo → get a risk score, 7-day
  favorability chart, and the alert message.

## Evaluation & Validation Plan
1. **Model accuracy**: held-out test set accuracy/F1 per pest class.
2. **Risk engine backtesting**: run the risk engine against *historical*
   weather data for regions/seasons with known past outbreaks; check whether
   HIGH-risk periods preceded documented outbreaks.
3. **Field pilot**: deploy with a small group of farmers/extension workers,
   compare warned vs. unwarned plots for pest-related yield loss.
4. **Threshold calibration**: tune `PEST_PROFILES` ranges and the HIGH/
   MODERATE/LOW cutoffs using local agri-extension expertise and pilot
   results rather than the illustrative defaults shipped here.

## Future Improvements
- Replace rule-based risk fusion with a trained model (e.g., gradient
  boosting) once enough labeled historical outbreak + weather data exists.
- Add satellite/remote-sensing vegetation indices (NDVI) as an additional
  signal for pests that follow vegetation flushes (e.g., locusts).
- Multi-day weather *trend* features (e.g., cumulative rainfall over past 10
  days) rather than only forward forecast.
- On-device (TFLite) version of the detection model for offline rural use.
