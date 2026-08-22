# Pest Detection with Weather-Based Early Warning

An end-to-end system that (1) detects crop pests from leaf/field images using a
CNN classifier, and (2) combines that detection with **regional weather data**
to issue an **early-warning risk score** before an infestation spreads —
because most pests only become active/reproduce under specific
temperature-humidity-rainfall windows.

## 1. Problem Statement
Farmers usually notice pest damage only after visible crop loss. Weather
conditions (temperature, humidity, rainfall, wind) are strong leading
indicators of pest outbreaks (e.g., aphids favor warm+humid spells, locusts
favor post-rain vegetation flushes, fungal-vector pests favor high humidity).
This project fuses **image-based pest detection** with a **weather-driven risk
model** to warn farmers 3–7 days before conditions become favorable for an
outbreak, not just after pests are visually confirmed.

## 2. System Architecture

```
                ┌────────────────────┐
                │   Field Images      │  (farmer app / camera trap)
                └─────────┬───────────┘
                          │
                 ┌────────▼─────────┐
                 │  Pest Detection    │  CNN (MobileNetV2 transfer learning)
                 │  Model (predict.py)│  → pest class + confidence
                 └────────┬───────────┘
                          │
                ┌─────────▼─────────┐        ┌──────────────────────┐
                │   Risk Engine       │◄───────│ Regional Weather API │
                │  (risk_engine.py)   │        │ (weather_api.py)     │
                └─────────┬───────────┘        └──────────────────────┘
                          │
                ┌─────────▼──────────┐
                │  Early Warning /     │
                │  Alert System        │  SMS / Email / Dashboard
                │ (alert_system.py)    │
                └─────────┬────────────┘
                          │
                ┌─────────▼──────────┐
                │  Streamlit Dashboard │  (app.py)
                └──────────────────────┘
```

## 3. Project Files

```
pest_early_warning/
├── README.md                    # this file
├── requirements.txt             # python dependencies
├── data/
│   ├── train/ val/ test/        # pest image dataset (class-per-folder)
├── models/
│   └── pest_cnn_model.h5        # trained model (generated after training)
├── logs/
│   └── alerts.log               # alert history
├── src/
│   ├── data_preprocessing.py    # image loading, augmentation, split
│   ├── model_train.py           # CNN training (transfer learning)
│   ├── predict.py               # single-image / batch inference
│   ├── weather_api.py           # fetch live weather for a region
│   ├── risk_engine.py           # fuses detection + weather -> risk score
│   └── alert_system.py          # generates & logs/send early warnings
├── app.py                       # Streamlit dashboard (end-to-end demo)
└── docs/
    └── process_flow.md          # detailed methodology & evaluation plan
```

## 4. Process Overview (5 stages)

1. **Data Collection & Preprocessing** — pest image dataset (e.g., PlantVillage,
   IP102, or field-collected images), labeled by pest species; resized,
   normalized, augmented (`data_preprocessing.py`).
2. **Pest Detection Model** — transfer-learning CNN (MobileNetV2 backbone)
   fine-tuned on the pest classes; outputs pest type + confidence
   (`model_train.py`, `predict.py`).
3. **Regional Weather Ingestion** — pulls live/forecast weather (temperature,
   humidity, rainfall, wind) for the farm's lat/long from a free API
   (Open-Meteo, no key required) (`weather_api.py`).
4. **Risk Fusion Engine** — rule-based + weighted scoring model that maps
   weather variables to pest-favorability scores per species (using known
   agronomy thresholds), combined with detection confidence and recent trend,
   to output a 0–100 risk score and risk level (`risk_engine.py`).
5. **Early Warning & Alerting** — when risk crosses a threshold, generates a
   human-readable alert with recommended action, logs it, and can push via
   email/SMS webhook stub (`alert_system.py`). All tied together in a live
   dashboard (`app.py`).

See `docs/process_flow.md` for the detailed methodology, evaluation metrics,
and future improvements.

## 5. Quick Start

```bash
pip install -r requirements.txt

# 1. Preprocess data (expects data/train/<class>/*.jpg etc.)
python src/data_preprocessing.py

# 2. Train the pest detection model
python src/model_train.py

# 3. Run a prediction on a single image
python src/predict.py --image path/to/leaf.jpg

# 4. Fetch weather + compute risk for a region
python src/risk_engine.py --lat 15.48 --lon 78.49 --pest aphid

# 5. Launch the full interactive dashboard
streamlit run app.py
```

## 6. Tech Stack
- **Model**: TensorFlow/Keras (MobileNetV2 transfer learning)
- **Weather**: Open-Meteo REST API (free, no auth)
- **Risk Engine**: rule-based weighted scoring (explainable, no black box)
- **Dashboard**: Streamlit
- **Alerts**: logging + pluggable email/SMS (Twilio/SendGrid stubs)

## 7. Notes
- Replace `data/` with your actual labeled pest image dataset before training.
- `weather_api.py` uses Open-Meteo (https://open-meteo.com), which needs no
  API key — good for prototypes; swap in a paid provider for production SLAs.
- Pest-weather favorability thresholds in `risk_engine.py` are illustrative;
  calibrate them with local agricultural-extension data for real deployment.
