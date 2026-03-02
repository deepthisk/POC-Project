import os
import boto3

# environment variables required by the embedding helper
QS_ACCOUNT = os.environ.get("QUICKSIGHT_ACCOUNT_ID")
QS_DASHBOARD_ID = os.environ.get("QUICKSIGHT_DASHBOARD_ID")
# for Q embedding you may need: QS_NAMESPACE, QS_USER_ARN, etc.

_client = boto3.client("quicksight")


def get_dashboard_embed_url():
    """Return an embed URL for the configured dashboard.
    The calling code can return this string in a JSON response.  See
    https://docs.aws.amazon.com/quicksight/latest/user/get-dashboard-embed-url.html

    Requires these environment variables:
      * QUICKSIGHT_ACCOUNT_ID
      * QUICKSIGHT_DASHBOARD_ID
      * (optionally) QUICKSIGHT_IDENTITY_TYPE, QS_USER_ARN, etc.
    """
    if not QS_ACCOUNT or not QS_DASHBOARD_ID:
        raise RuntimeError("QUICKSIGHT_ACCOUNT_ID and QUICKSIGHT_DASHBOARD_ID must be set")

    resp = _client.get_dashboard_embed_url(
        AwsAccountId=QS_ACCOUNT,
        DashboardId=QS_DASHBOARD_ID,
        # IdentityType="IAM" or "QUICKSIGHT" depending on how you manage users
        # SessionLifetimeInMinutes=600,
        # UndoRedoDisabled=False,
    )
    return resp["EmbedUrl"]


def get_q_anonymous_embed_url():
    """Return an embed URL for QuickSight Q using the anonymous‑user API.

    This is useful when you want to expose Q to end users without requiring
    they log in to QuickSight.  The URL has a short lifetime (minutes).

    Required environment variables:
      * QUICKSIGHT_ACCOUNT_ID
      * QUICKSIGHT_NAMESPACE   (often "default")
      * QUICKSIGHT_IDENTITY_TYPE (usually "ANONYMOUS")
      * QUICKSIGHT_SESSION_NAME (unique per session, e.g. a random UUID)
      * QUICKSIGHT_Q_ROLE_ARN  (an IAM role with the policies needed for Q)
    Optional:
      * QS_Q_ID  (if you want to target a specific Q experience)

    For details see: https://docs.aws.amazon.com/quicksight/latest/APIReference/API_GenerateEmbedUrlForAnonymousUser.html
    """
    namespace = os.environ.get("QUICKSIGHT_NAMESPACE", "default")
    session_name = os.environ.get("QUICKSIGHT_SESSION_NAME")
    role_arn = os.environ.get("QUICKSIGHT_Q_ROLE_ARN")
    q_id = os.environ.get("QS_Q_ID")

    if not QS_ACCOUNT or not namespace or not session_name or not role_arn:
        raise RuntimeError("Missing one of QUICKSIGHT_ACCOUNT_ID, QUICKSIGHT_NAMESPACE, QUICKSIGHT_SESSION_NAME, QUICKSIGHT_Q_ROLE_ARN")

    params = {
        "AwsAccountId": QS_ACCOUNT,
        "Namespace": namespace,
        "SessionName": session_name,
        "IdentityType": "ANONYMOUS",
        "AuthorizedResourceArns": [
            # optionally restrict to certain dashboards or analyses
        ],
        "SessionLifetimeInMinutes": 600,
        "AllowedDomains": ["*"]
    }
    if q_id:
        params["QEmbeddingConfig"] = {"InitialTopicId": q_id}

    resp = _client.generate_embed_url_for_anonymous_user(**params)
    return resp["EmbedUrl"]


def get_q_embed_url():
    """Simplified wrapper for whichever embed method you choose.

    Currently returns the anonymous Q URL, but you may adjust logic to decide
    between dashboard vs Q vs IAM user embedding.
    """
    return get_q_anonymous_embed_url()
