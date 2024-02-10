# Adapted from servicenow.itsm module_utils client
# https://github.com/ansible-collections/servicenow.itsm/blob/b7c5e49aa6147fe5cd1b935a36a9ed385caa0e19/plugins/module_utils/client.py

# from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
# from ansible.module_utils.six.moves.urllib.parse import quote, urlencode
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from http.client import HTTPResponse
from ansible.module_utils.urls import Request
from ..module_utils.errors import TMDBAuthException, TMDBException, TMDBResponseException

TMDB_BASE_URL = "https://api.themoviedb.org"

class TMDBClient():
    def __init__(
        self,
        api_url,
        api_key=None,
        username=None,
        password=None,
        account_id=None,
        **kwargs
    ):
        if not (api_url or "").startswith((TMDB_BASE_URL)):
            raise TMDBException(
                f"Invalid instance api_url value: '{api_url}'. "
                f"Value must start with {TMDB_BASE_URL}"
            )

        self.api_url = api_url
        self.api_key = api_key
        self.username = username
        self.password = password
        self.account_id = account_id
        self.session_id = None

        self._client = Request()

    def _get_request_token(self) -> str:
        path = "/authentication/token/new"
        params = {"api_key": self.api_key}
        resp = self.request('get', path=path, params=params)

        if resp.status != 200:
            raise TMDBResponseException(f"Failed to create request token: status code {resp.status}")
        
        data = json.loads(resp.read())
        return data['request_token']
    
    def _validate_token(self, request_token: str) -> None:
      path = "/authentication/token/validate_with_login"
      params = {"api_key": self.api_key}
      body = dict(
          username=self.username,
          password=self.password,
          request_token=request_token
      )
      resp = self.request('post', path=path, params=params, data=body)

      if resp.status != 200:
            raise TMDBResponseException(f"Failed to validate request token: status code {resp.status}")
      
    def _create_session(self, request_token) -> str:
      path = "/authentication/session/new"
      params = {"api_key": self.api_key}
      body = dict(request_token=request_token)
      resp = self.request('post', path=path, params=params, data=body)

      if resp.status != 200:
            raise TMDBResponseException(f"Failed to create new session: status code {resp.status}")
      
      data = json.loads(resp.read())
      return data['session_id']

    def login(self) -> None:
        if not (self.api_key and self.username and self.password):
            raise TMDBAuthException(
                f"Missing input parameters (one of):"
                f"tmdb_api_key, tmdb_username, tmdb_password"
            )
        
        try:
            request_token = self._get_request_token()
            self._validate_token(request_token)
            session_id = self._create_session(request_token)
            self.session_id = session_id
        except Exception as e:
          raise TMDBAuthException(e)

    def _request(self, method, path, data=None, headers=None) -> HTTPResponse:
        try:
            raw_resp = self._client.open(
                method,
                path,
                data=data,
                headers=headers
            )
        except HTTPError as e:
            if e.code == 401:
                raise TMDBAuthException(f"Failed to authenticate with the instance: {e.code} {e.reason}")
            raise TMDBException(e)
        except URLError as e:
            raise TMDBException(e.reason)

        return raw_resp

    def request(self, method, path, params={}, data=None, headers=None, bytes=None) -> HTTPResponse:
        # Make sure we only have one kind of payload
        if data is not None and bytes is not None:
            raise AssertionError(
                "Cannot have JSON and binary payload in a single request."
            )

        url = f"{self.api_url}{path}?"
        if self.session_id:
            params['api_key'] = self.api_key
            params['session_id'] = self.session_id
        if len(params):
            url += urlencode(params)
        headers = dict(headers or dict(Accept="application/json"))
        if data is not None:
            data = json.dumps(data, separators=(",", ":"))
            headers["Content-type"] = "application/json"
        elif bytes is not None:
            data = bytes
        return self._request(method, url, data=data, headers=headers)

    def get(self, path, params={}):
        resp = self.request("GET", path, params=params)
        if resp.status in (200, 404):
            return resp
        raise TMDBResponseException(resp.status, resp.data)

    def post(self, path, data, params={}):
        resp = self.request("POST", path, data=data, params=params)
        if resp.status in [200,201]:
            return resp
        raise TMDBResponseException(resp.status, resp.data)

    def patch(self, path, data, params={}):
        resp = self.request("PATCH", path, data=data, params=params)
        if resp.status == 200:
            return resp
        raise TMDBResponseException(resp.status, resp.data)

    def put(self, path, data, params={}):
        resp = self.request("PUT", path, data=data, params=params)
        if resp.status == 200:
            return resp
        raise TMDBResponseException(resp.status, resp.data)

    def delete(self, path, params={}):
        resp = self.request("DELETE", path, params=params)
        if resp.status != 204:
            raise TMDBResponseException(resp.status, resp.data)