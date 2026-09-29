"""Small authenticated REST transport with explicit failures and no redirects."""

from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from azure.identity import get_bearer_token_provider

from lab.config import LabError


SEARCH_SCOPE = "https://search.azure.com/.default"
ARM_SCOPE = "https://management.azure.com/.default"


class CloudRequestError(LabError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class JsonResult:
    body: dict
    status: int
    etag: str | None


class JsonHttp:
    def __init__(self, credential, *, scope: str, allowed_origin: str):
        self.token = get_bearer_token_provider(credential, scope)
        self.origin = urlsplit(allowed_origin)
        self.opener = build_opener(_NoRedirect())

    def request(self, method: str, url: str, payload: dict | None = None, *, etag: str | None = None, create_only: bool = False) -> JsonResult:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != self.origin.netloc or parsed.username or parsed.password:
            raise LabError("인증 정보를 승인된 Azure endpoint 외부로 전송하지 않습니다.")
        headers = {"Authorization": f"Bearer {self.token()}", "Accept": "application/json"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if etag is not None:
            headers["If-Match"] = etag
        if create_only:
            headers["If-None-Match"] = "*"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=180) as response:
                status = response.status
                text = response.read().decode("utf-8")
                response_etag = response.headers.get("ETag")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:1800]
            raise CloudRequestError(exc.code, f"{method} {parsed.path}: HTTP {exc.code}\n{body}") from exc
        except (URLError, TimeoutError) as exc:
            raise LabError(f"{method} {parsed.path}: 네트워크 오류. 자동 재시도하지 않았습니다: {exc}") from exc
        if not text and (status == 204 or (method == "DELETE" and status in {200, 202})):
            return JsonResult({}, status, response_etag)
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LabError(f"{method} {parsed.path}: JSON이 아닌 서비스 응답입니다.") from exc
        if not isinstance(value, dict):
            raise LabError(f"{method} {parsed.path}: 예상한 JSON 객체 응답이 아닙니다.")
        return JsonResult(value, status, response_etag or value.get("@odata.etag"))
