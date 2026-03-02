import json
import os

# helpers that wrap AWS services
from bedrock_utils import text_to_sql
from athena_utils import run_athena_query

# a simple static schema example passed to the LLM
DEFAULT_SCHEMA = """
metrics (
    timestamp string,
    publisher string,
    metric_name string,
    value double
)
"""


def analyze_results(rows, user_text):
    """Basic post‑query inspection. Returns a status field that the caller
    (the lambda handler) can use to decide whether an anomaly occurred.

    For this POC we look for any negative or large negative 'value' fields
    when the user asked about a drop/anomaly.  A real implementation would
    use history, averages, etc.  """
    if "anomaly" in user_text.lower() or "drop" in user_text.lower():
        for row in rows:
            try:
                val = float(row.get("value", 0))
                if val < 0 or val < -15:
                    return {"status": "🚨 ANOMALY", "details": row}
            except ValueError:
                continue
    return {"status": "✅ NORMAL", "details": rows[:1] if rows else None}


def lambda_handler(event, context):
    # simple router based on path; API Gateway proxy integration
    path = event.get("rawPath") or event.get("path") or ""
    if path.endswith("/get-q-embed-url"):
        # return a URL that the front‑end can use to embed QuickSight
        try:
            from quicksight_utils import get_dashboard_embed_url
            url = get_dashboard_embed_url()
            return {"statusCode": 200, "body": json.dumps({"url": url})}
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    # otherwise fall through to text->SQL query endpoint
    # accept either POSTed JSON or a query string parameter 'q'
    body = {}
    try:
        if event.get("body"):
            body = json.loads(event["body"])
    except json.JSONDecodeError:
        pass

    user_text = body.get("query") or (event.get("queryStringParameters") or {}).get("q")
    if not user_text:
        return {"statusCode": 400, "body": json.dumps("Missing 'query' parameter")}

    # convert natural language into SQL via Bedrock
    sql = text_to_sql(user_text, DEFAULT_SCHEMA)

    # execute the generated statement
    try:
        rows = run_athena_query(sql)
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    analysis = analyze_results(rows, user_text)

    response = {"sql": sql, "rows": rows, "analysis": analysis}
    return {"statusCode": 200, "body": json.dumps(response)}
