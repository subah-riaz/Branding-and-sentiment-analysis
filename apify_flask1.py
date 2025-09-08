from flask import Flask, request, jsonify
from apify_client import ApifyClient
from transformers import pipeline
import sqlite3
import time


API_TOKEN = "Your API Key"

client = ApifyClient(API_TOKEN)
app = Flask(__name__)





def scrape_comments_by_brand(brand_name):
    all_video_urls = []
    run_input = {"hashtags": [brand_name], "resultsPerPage": 100}

    try:
        run = client.actor("clockworks/free-tiktok-scraper").call(run_input=run_input)
        dataset_id = run["defaultDatasetId"]
        dataset_items = list(client.dataset(dataset_id).iterate_items())

        for item in dataset_items:
            video_url = item.get("webVideoUrl")
            if video_url:
                all_video_urls.append(video_url)
    except Exception as e:
        print(f"Error scraping #{brand_name}: {e}")
        return None

    time.sleep(10)  

    if all_video_urls:
        try:
            comment_input = {
                "postURLs": all_video_urls,
                "commentsPerPost": 30,
                "maxRepliesPerComment": 0,
                "resultsPerPage": 40
            }

            comment_run = client.actor("clockworks/tiktok-comments-scraper").call(run_input=comment_input)
            comments_dataset_id = comment_run["defaultDatasetId"]
            return comments_dataset_id

        except Exception as e:
            print(f"Error scraping comments: {e}")
            return None
    else:
        return None


def analyze_sentiments(dataset_id):
    dataset = client.dataset(dataset_id)

    all_comments = []
    for item in dataset.iterate_items():
        comment = item.get("text")
        if comment:
            all_comments.append(comment)

    cleaned_comments = list(set(filter(None, all_comments)))

    total_comments = len(all_comments)
    cleaned_comments = list(set(filter(None, all_comments)))
    num_cleaned_comments = len(cleaned_comments)


    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment"
    )

    label_map = {
        "LABEL_0": "Negative",
        "LABEL_1": "Neutral",
        "LABEL_2": "Positive"
    }

    
    conn = sqlite3.connect("sentiment_results.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Sentiments (
        comment TEXT,
        sentiment TEXT,
        score REAL
    )
    """)
    conn.commit()

    sentiment_results = {
        "Positive": 0,
        "Neutral": 0,
        "Negative": 0
    }

    for comment in cleaned_comments:
        result = sentiment_pipeline(comment)[0]
        label = label_map[result["label"]]
        score = result["score"]
        sentiment_results[label] += 1

        # Insert into DB
        cursor.execute(
            "INSERT INTO Sentiments (comment, sentiment, score) VALUES (?, ?, ?)",
            (comment, label, score)
        )

    conn.commit()
    conn.close()

    return {
    "sentiment_counts": sentiment_results,
    "total_comments": total_comments,
    "cleaned_comments": num_cleaned_comments
    }


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    brand = data.get("brand")

    if not brand:
        return jsonify({"error": "Brand name is required"}), 400

    dataset_id = scrape_comments_by_brand(brand)
    if not dataset_id:
        return jsonify({"error": "Scraping failed"}), 500

    
    sentiment_data = analyze_sentiments(dataset_id)
    return jsonify({
        "brand": brand,
        "dataset_id": dataset_id,
        "sentiments": sentiment_data["sentiment_counts"],
        "total_comments": sentiment_data["total_comments"],
        "cleaned_comments": sentiment_data["cleaned_comments"],
        
        })

@app.route('/results', methods=['GET'])
def get_all_results():
    conn = sqlite3.connect("sentiment_results.db")
    cursor = conn.cursor()
    cursor.execute("SELECT comment, sentiment, score FROM Sentiments")
    rows = cursor.fetchall()
    conn.close()

    results = [
        {"comment": row[0], "sentiment": row[1], "score": round(row[2], 4)}
        for row in rows
    ]

    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(debug=True)




