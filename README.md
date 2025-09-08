# Branding-and-sentiment-analysis
# TikTok Brand Sentiment Analysis API

This project is a **Flask-based web API** that scrapes TikTok comments for a given brand hashtag, analyzes their sentiment using a transformer model, and stores the results in a SQLite database. It provides endpoints to run new analyses and retrieve stored results.

---

##  Features
- Scrapes TikTok videos and comments by brand hashtag (via Apify).
- Performs sentiment analysis (Positive, Neutral, Negative) using HuggingFace's `cardiffnlp/twitter-roberta-base-sentiment` model.
- Stores results (comment, sentiment, confidence score) in a local SQLite database.
- Provides REST API endpoints to:
  - Run new analysis for a brand.
  - Retrieve all past results from the database.

---

##  Technologies Used
- **Python**
- **Flask** – for building the web API
- **Apify Client** – for TikTok scraping
- **Transformers (HuggingFace)** – for sentiment analysis
- **SQLite3** – for storing results

---

##  API Endpoints

### 1. Analyze Brand Sentiment
`POST /analyze`

- **Request body:**
```json
{
  "brand": "Nike"
}
