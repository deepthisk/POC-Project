import os
import time

import boto3

# configuration via environment variables with sensible defaults
DATABASE = os.environ.get("ATHENA_DATABASE", "default")
OUTPUT = os.environ.get("ATHENA_OUTPUT_S3", "s3://my-athena-results/")

_athena = boto3.client("athena")


def run_athena_query(query: str) -> list[dict]:
    """Submit a query to Athena and wait for the results, returning a list of rows.

    This is a very simple wrapper; for production you may want to cache
    executions, stream results with pagination, or use async SNS callbacks.
    """
    resp = _athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": DATABASE},
        ResultConfiguration={"OutputLocation": OUTPUT},
    )
    qid = resp["QueryExecutionId"]

    # poll until the query finishes
    while True:
        status = _athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]["State"]
        if status in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)

    if status != "SUCCEEDED":
        raise RuntimeError(f"Athena query failed with status {status}")

    results = _athena.get_query_results(QueryExecutionId=qid)
    cols = [c["Label"] for c in results["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
    rows = []
    for r in results["ResultSet"]["Rows"][1:]:  # skip header row
        vals = [d.get("VarCharValue") for d in r["Data"]]
        rows.append(dict(zip(cols, vals)))
    return rows
