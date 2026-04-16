import logging

import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request
from google.oauth2 import credentials as oauth2_credentials
from google.oauth2 import id_token

from ..cache import make_hashable, timed_lru_cache
from .exceptions import InvalidCredentialsOAuth2

ENV_VAR_GOOGLE_APPLICATION_CREDENTIALS = "GOOGLE_APPLICATION_CREDENTIALS"
DEFAULT_SCOPES_FOR_IMPERSONATED_SERVICE_ACCOUNT = {
    "openid",
    "email",
    "https://www.googleapis.com/auth/iam",
    "https://www.googleapis.com/auth/cloud-platform",
}
TOKEN_LIFETIME = 3600
SA_CREDENTIAL_CACHE_LIFETIME_SECONDS = 900


@make_hashable
@timed_lru_cache(seconds=SA_CREDENTIAL_CACHE_LIFETIME_SECONDS)
def _get_impersonated_credentials(
    target_service_account: str, scopes: set[str] | None = None
) -> impersonated_credentials.Credentials | google.auth.credentials.Credentials:
    """Helper function to fetch Impersonated Service Account credentials,
    using the local environment's ADC credentials (ADC creds must have access to impersonate target service account)

    :param target_service_account: str of Service Account to get Impersonated Credentials for
    :param scopes: Set[str] e.g. {"https://www.googleapis.com/auth/spreadsheets.readonly"}
    :return: google.auth.impersonated_credentials.Credentials (impersonated service account credentials),
    or google.auth.credentials.Credentials (if target_service_account is the same as the ADC credentials)
    """
    scopes = scopes or set()
    target_scopes: list[str] = list(DEFAULT_SCOPES_FOR_IMPERSONATED_SERVICE_ACCOUNT.union(scopes))

    logging.info(f"Fetching Impersonated Credentials for Service Account: {target_service_account}")

    source_credentials, project_id = google.auth.default(scopes=target_scopes)
    source_credentials.refresh(Request())

    if hasattr(source_credentials, "service_account_email"):
        # Note "service_account_email" is not guaranteed to be set until refresh() has been called.
        if source_credentials.service_account_email == target_service_account:
            return source_credentials

    target_impersonated_credentials = impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=target_service_account,
        target_scopes=target_scopes,
        lifetime=TOKEN_LIFETIME,
    )
    target_impersonated_credentials.refresh(Request())
    return target_impersonated_credentials


@timed_lru_cache(seconds=SA_CREDENTIAL_CACHE_LIFETIME_SECONDS)
def _get_impersonated_id_token(
    target_service_account: str,
    target_audience: str,
) -> str:
    """Get ID Token of an Impersonated Service Account credential

    :param target_service_account: str of Service Account to get Impersonated Credentials for
    :param target_audience: the URL or IAP Client ID to include in token, e.g. "https://www.example.com"
    :return: an ID Token that can be used to make a request to an authenticated service
    """

    logging.info(f"Fetching Impersonated ID Token for Service Account: {target_service_account}")

    target_credentials = _get_impersonated_credentials(target_service_account=target_service_account)

    # If ADC is already the target SA, _get_impersonated_credentials returns the source
    # credentials directly — use fetch_id_token instead of IDTokenCredentials.
    if not isinstance(target_credentials, impersonated_credentials.Credentials):
        return id_token.fetch_id_token(Request(), audience=target_audience)

    idt_credentials = impersonated_credentials.IDTokenCredentials(
        target_credentials=target_credentials,
        target_audience=target_audience,
        include_email=True,
    )
    idt_credentials.refresh(Request())
    return idt_credentials.token


@make_hashable
@timed_lru_cache(seconds=SA_CREDENTIAL_CACHE_LIFETIME_SECONDS)
def get_credentials(
    target_service_account: str, scopes: set[str] | None = None
) -> impersonated_credentials.Credentials | google.auth.credentials.Credentials:
    """Will return impersonated credentials for specified service account, if user is authorized for that service account, otherwise will use ADC Credentials.
    If ADC credentials are OAuth2 credentials will raise an error, since these are not valid Service Account Credentials.

    Behavior
        - Will attempt to impersonate target_service_account if passed as a function argument
        - If environment variables are not set will default to ADC Credentials

    :param target_service_account: string of Service Account email to fetch credentials for
    :param scopes: Set[str] e.g. {"https://www.googleapis.com/auth/spreadsheets.readonly"}
        the following scopes are set by default:
            [
                "openid",
                "email",
                "https://www.googleapis.com/auth/iam",
                "https://www.googleapis.com/auth/cloud-platform",
            ]
    :return: google.auth.impersonated_credentials.Credentials (impersonated service account credentials),
    or google.auth.credentials.Credentials (if target_service_account is the same as the ADC credentials)
    """

    scopes = scopes or set()
    target_scopes: list[str] = list(DEFAULT_SCOPES_FOR_IMPERSONATED_SERVICE_ACCOUNT.union(scopes))

    if target_service_account:
        creds = _get_impersonated_credentials(target_service_account=target_service_account, scopes=target_scopes)
    else:
        source_credentials, _ = google.auth.default(scopes=target_scopes)
        if isinstance(source_credentials, oauth2_credentials.Credentials):
            raise InvalidCredentialsOAuth2(
                f"ADC are OAuth Credentials set env var for {ENV_VAR_GOOGLE_APPLICATION_CREDENTIALS}"
            )
        creds = source_credentials

    creds.refresh(Request())
    return creds


def get_identity_token(target_audience: str, target_service_account: str | None = None) -> str:
    """Obtain an OpenID Connect (OIDC) token that can be used to request an authenticated service.
    Works for services protected by Identity-Aware Proxy (IAP), by passing the token to the Authorization header as a Bearer token.

    Behavior
        - Will attempt to impersonate target_service_account if passed as a function argument,
        - If target_service_account is not passed, look for service account in environment variable GOOGLE_APPLICATION_CREDENTIALS,
        - If environment variables are not set will default to ADC Credentials
        - Will infer service account from compute engine service account if available
        - Will use service account defined by GOOGLE_APPLICATION_CREDENTIALS

    :param target_audience: the URL or IAP Client ID to include in token, e.g. "https://www.example.com"
    :param target_service_account: optional string of Service Account email to fetch credentials for,
            if None provided will try getting Service Account to impersonate from the local environment
    :return: str of ID Token that can be used to request an authenticated service
    """

    if target_service_account:
        sa_id_token = _get_impersonated_id_token(
            target_service_account=target_service_account,
            target_audience=target_audience,
        )
        return sa_id_token
    return id_token.fetch_id_token(Request(), audience=target_audience)