This is read me notes
# 🤖 Analytics Agent

An AI-powered business intelligence agent built with **Amazon Bedrock**, **AWS Lambda**, and **Amazon Athena**.

## 🎯 Project Overview
This agent automates daily business reporting by:
1. Querying raw data using SQL via Amazon Athena.
2. Generating natural language summaries (Successes, Anomalies, and Facts).
3. Posting insights to a DynamoDB dashboard and sending alerts via Slack/Email.

## 🛠️ Tech Stack
* **Language:** Python 3.12+
* **AI Orchestration:** Amazon Bedrock Agents
* **Database:** Amazon DynamoDB (Insight Store)
* **Compute:** AWS Lambda
* **Visualization:** Amazon QuickSight

## 🚀 Getting Started
Follow these steps to run the POC locally and deploy the Lambda:

1. **Install dependencies**
   ```sh
   python -m venv .venv            # optional virtual env
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   Alternatively, the CloudFormation template below contains an inline stub
   for the function.  You can replace that with a packaged ZIP of the
   repository code.

2. **Configure AWS credentials** (via `~/.aws/credentials` or environment variables).

3. **Set required environment variables** for the Lambda (examples below):
   ```sh
   export ATHENA_DATABASE=mydb
   export ATHENA_OUTPUT_S3=s3://my-bucket/athena-results/
   export BEDROCK_MODEL=claude-sonnet-3.6
# QuickSight settings
export QUICKSIGHT_ACCOUNT_ID=123456789012
export QUICKSIGHT_DASHBOARD_ID=abcd-ef01-2345-6789
# for anonymous Q embedding
export QUICKSIGHT_NAMESPACE=default
export QUICKSIGHT_SESSION_NAME=$(uuidgen)
export QUICKSIGHT_Q_ROLE_ARN=arn:aws:iam::123456789012:role/QuickSightQAnonymous
export QS_Q_ID=<optional-topic-or-q-id>
   ```

4. **Deploy** the handler using your preferred method (Serverless Framework, SAM,
   CloudFormation, or `aws lambda create-function`/`update-function-code`).

   To deploy with CloudFormation:
   ```sh
   aws cloudformation deploy \
     --template-file template.yaml \
     --stack-name analytics-agent-poc \
     --capabilities CAPABILITY_NAMED_IAM \
     --parameter-overrides AthenaDatabase=mydb AthenaOutputS3=s3://my-bucket/athena-results/
   ```

   After deployment, the `ApiEndpoint` output points at the POST `/query`
   URL.

5. **Invoke** via API Gateway: send a JSON payload with `query` or use `?q=`.

### 🧪 Local testing
(This is the same as before; API Gateway is not required for local runs.)
You can run the handler directly:
```python
from lambda_function import lambda_handler

event = {"body": json.dumps({"query": "show me the last hour of impressions"})}
print(lambda_handler(event, None))
```

Environment variables must be set in the shell before running.

### ✅ Testing the full POC
1. **Prepare Athena data**
   * Ensure your Athena table contains sample rows for the metrics you care about.
   * Verify manually with an `aws athena start-query-execution` call if needed.
2. **Deploy the Lambda/API** using the CloudFormation template (or SAM) with
   all environment variables configured, including QuickSight settings.
3. **Confirm Bedrock SQL translation**
   * POST a test prompt to `/query` (curl, Postman or the UI textarea).
   * Confirm the response JSON shows a valid SQL statement and returns rows
     from Athena.
4. **Verify anomaly detection logic**
   * Craft queries that should trigger your threshold rules (e.g. values < -15).
   * Check that the `analysis.status` field in the response updates to
     `🚨 ANOMALY` or `✅ NORMAL` accordingly.
5. **QuickSight Q flow**
   * Build a QuickSight analysis or Q topic over the same Athena dataset.
   * Hit `/get-q-embed-url` to fetch an embed URL and open it in a browser
     (you can also use the sample `ui/index.html` page).
   * Ask natural‑language questions in the embedded Q interface and verify
     answers match expectations.
6. **Integrated UI exercise**
   * Host the `ui/` directory (S3/CloudFront or local server) and point its
     fetch endpoints at your deployed API.
   * Use the textarea to exercise the Bedrock agent; results appear below.
   * The QuickSight embed should load side‑by‑side, allowing both Q and API
     queries in a single screen.
7. **End‑to‑end sanity check**
   * Have a colleague run through the flows to ensure consistent behavior and
     that embed tokens refresh correctly after expiration.

This sequence ensures the backend, AI translation, Athena access, anomaly
logic and embedded UI are all working together as a cohesive prototype.

### 🧱 Project skeleton
Here's the structure of the POC repository:

```
POC-Project/
├── lambda_function.py        # main Lambda handler
├── bedrock_utils.py         # helper for Bedrock text→SQL
├── athena_utils.py          # helper for executing Athena queries
├── requirements.txt         # Python dependencies
├── README.md                # this documentation
└── .gitignore               # ignores for Python/Lambda artifacts
```

You can extend this layout with deployment templates, tests, or support modules.

## 🔍 Targeted Anomalies

---

## 🧩 QuickSight Q & UI integration
The long‑term goal is a unified interface that serves both engineering and
business users.  

* The Lambda/Bedrock agent powers natural‑language queries behind the scenes.
* **QuickSight Q** can be embedded in a web dashboard to allow deep dives with
  conversational analytics; the same Bedrock model can back Q and the API.
* A simple front‑end (React/Vue/HTML) can host the embedded QuickSight chart
  plus an input box that calls the `/query` endpoint directly for engineers.
  
This repo currently contains only the backend pieces.  You can add an
`ui/` directory with HTML/JS that uses the [`amazon-quicksight-embedding-sdk`](https://docs.aws.amazon.com/quicksight/latest/user/embedding-sdk.html)
or a lightweight page that hits the API and displays JSON results.

Existing functionality will let business users hit Q for natural language
metrics while technical users can craft their own prompts using the REST API.

### 📁 UI example
A simple front‑end lives under `ui/index.html`:

* Embeds QuickSight Q (you must implement a backend endpoint `GET /get-q-embed-url`
  that returns a JSON object with an `url` field containing the dashboard or
  Q session embed URL).
* Provides a textarea/button for engineers to POST directly to `/query` and
  displays the resulting JSON.

You can serve the `ui` directory with any static host (S3/CloudFront or a
small Express/Flask app) and configure CORS as needed.  The sample page
is purely illustrative and meant to show the “center place” UI you mentioned.

### How it works
1. **User interaction** – either a business user types a question into QuickSight
   Q (embedded via our UI) or an engineer submits a prompt through `/query`.
2. **Lambda backend** receives the request; if `/query`, it forwards the text to
   Bedrock using `bedrock_utils.text_to_sql`.
3. **Bedrock model** returns an SQL statement based on the provided Athena
   schema.
4. **Athena util** runs the SQL and returns result rows.
5. **Post‑processing** (`analyze_results`) flags anomalies using simple rules.
6. Response is returned to the caller, and business users can also explore the
   same data interactively in QuickSight.

### Next steps
* Hook up real Athena schema and credentials; remove mock example.
* Improve analysis logic (historical baselines, statistical detection).
* Add persistence (DynamoDB) for storing insights and sending alerts.
* Build out front‑end UI with authentication, styling, and embed lifecycle
  management.
* Add tests, CI/CD pipeline, and deployable package (SAM/serverless).

### What this supports
* **Engineers** – programmatic access to data via text queries and SQL
  generation; they can inspect SQL, modify it, or integrate it into workflows.
* **Business users** – conversational dashboarding through QuickSight Q or
  static dashboards derived from the same data.
* **Hybrid teams** – a single backend that serves both audiences and ensures
  analysis consistency across tools.

### Setting up anonymous QuickSight Q embedding
1. Create an IAM role (the `QUICKSIGHT_Q_ROLE_ARN`) that grants QuickSight
   permissions to describe analyses, dashboards, etc.
2. Enable anonymous embedding in your QuickSight account and note the
   namespace (often `default`).
3. Set environment variables listed above; the lambda will use them when
   generating URLs.
4. The front end will receive a temporary URL (valid ~10 minutes) and load
   Q without requiring users to sign in.

Our agent specifically monitors **Live Sports** programmatic traffic for:
* **Inventory Dips:** Bid request drops beyond a 15% threshold.
* **Delivery Fluctuations:** Under-delivering or over-delivering relative to game quarters.
* **Cost Volatility:** Significant shifts in SSP supply costs during peak viewership.
