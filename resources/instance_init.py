from requests import Session, Response
from requests.exceptions import SSLError
from time import sleep
import env

class Instance():
    def __new__(cls, *args, **kwargs):
        if cls is Instance:
            raise TypeError("base class may not be instantiated")
        return object.__new__(cls, *args, **kwargs)

    @staticmethod
    def verify_session(verify_api_endpoint: str, session: Session) -> None:
        r = session.get(verify_api_endpoint)
        if Instance.authorized(r.status_code) and r.status_code >= 400:
            exit(f'FATAL: Could not successfully interact with the api at {verify_api_endpoint} error: HTTP {r.status_code}. Closing...')

    @staticmethod
    def rate_limited(status_code: int) -> bool:
        if status_code == 429:
            print('WARN: Hit api rate limit, sleeping for 1 minute then attempting to resume...')
            sleep(60)
            return True
        return False

    @staticmethod
    def authorized(status_code: int) -> bool:
        if status_code == 401:
            exit('FATAL: Received "Unauthorized" (HTTP 401) response from your instance. '
                 'Please check your credentials and try again.')
        elif status_code == 403:
            exit('FATAL: Received "Forbidden" (HTTP 403) response from your instance. '
                 'Please ensure you have the necessary admin permissions '
                 'and that your client is IP whitelisted before trying again.')
        return True


class ServerInstance(Instance):
    def __init__(self):
        self.username = env.server_username
        self.password = env.server_password
        self.url = env.server_url
        self.api = f'{self.url}/rest/api/latest'
        self.ssl_verified = True
        self.session = Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({'Accept': 'application/json', 'Content-type': 'application/json'})
        self._verify_url()
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp45
        self.verify_session(f'{self.api}/admin/cluster', self.session)

    def _verify_url(self) -> None:
        try:
            r = self.get_api(f'{self.url}/status')
        except SSLError:
            self.ssl_verified = False # Using https but ssl cert is self-signed or other issue, ignorable
            r = self.get_api(f'{self.url}/status')

        if not "RUNNING" in r.text:
            exit(f'FATAL: Did not get a "RUNNING" response from the url "{self.url}/status", cannot continue. Closing...')

    def get_api(self, endpoint: str, params: dict=None) -> Response:
        while True:
            r = self.session.get(endpoint, params=params, verify=self.ssl_verified)

            if not self.rate_limited(r.status_code) and self.authorized(r.status_code):
                return r


class CloudInstance(Instance):
    def __init__(self):
        self.username = env.cloud_username
        self.password = env.cloud_password
        self.workspace = env.cloud_workspace
        self.url = f"https://bitbucket.org/{self.workspace}"
        self.api = "https://api.bitbucket.org"
        self.session = Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({'Accept': 'application/json', 'Content-type': 'application/json'})
        # https://developer.atlassian.com/bitbucket/api/2/reference/resource/workspaces/%7Bworkspace%7D/permissions
        self.verify_session(f'{self.api}/2.0/workspaces/{self.workspace}/permissions', self.session)

    def get_api(self, endpoint: str, params: dict=None) -> Response:
        while True:
            r = self.session.get(endpoint, params=params)

            if not self.rate_limited(r.status_code) and self.authorized(r.status_code):
                return r

    def post_api(self, endpoint: str, payload: dict) -> Response:
        while True:
            r = self.session.post(endpoint, data=payload)

            if not self.rate_limited(r.status_code) and self.authorized(r.status_code):
                return r

    def put_api(self, endpoint: str, payload: dict, data_method: str) -> Response:
        if data_method not in ["data", "json"]:
            raise ValueError('Incorrect usage of input "data_method" arg in .resources/instance_init.py "CloudInstance.put_api"')
        while True:
            if data_method == "data":
                # overwrite the default headers to plain text
                r = self.session.put(endpoint, data=payload, headers={'Content-type': 'text/plain'})
            else: # data_method = "json"
                r = self.session.put(endpoint, json=payload)

            if not self.rate_limited(r.status_code) and self.authorized(r.status_code):
                return r
