from requests import Session
from requests.exceptions import SSLError
import env
from resources.exceptions import InstanceNotAvailable

class Instance():
    def __init__():
        pass

    @staticmethod
    def set_session(username: str, password: str) -> Session:
        session = Session()
        session.auth = (username, password)
        return session

    @staticmethod
    def verify_session(api_url: str, session: Session):
        r = session.get(api_url)
        if r.status_code >= 400:
            raise InstanceNotAvailable(f'Could not successfully interact with the api at {api_url} with provided credentials.\n'
                                       'Please check your credentials and try again.')

class ServerInstance(Instance):
    def __init__(self):
        self.username = env.server_username
        self.password = env.server_password
        self.url = env.server_url
        self.api = f'{self.url}/rest/api/latest'
        self.session = self.set_session(self.username, self.password)
        self._verify_url()
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp45
        verify_api_endpoint = f'{self.api}/admin/cluster'
        self.verify_session(verify_api_endpoint, self.session)

    def _verify_url(self):
        try:
            r = self.session.get(f'{self.url}/status')
            self.ssl_verified = True #Using https and ssl cert is good
        except SSLError:
            self.ssl_verified = False # Using https and ssl cert is self-signed or other issue, ignorable
            r = self.session.get(f'{self.url}/status', verify=self.ssl_verified)

        if not "RUNNING" in r.text:
            raise InstanceNotAvailable(f'Did not get a "RUNNING" response from the url "{self.url}/status"')
        
    def get_api(self, endpoint=None, headers=None, params=None):
        r = self.session.get(endpoint, headers=headers, params=params, verify=self.ssl_verified)
        return r


class CloudInstance(Instance):
    def __init__(self):
        self.username = env.cloud_username
        self.password = env.cloud_password
        self.workspace = env.cloud_workspace
        self.cookie = env.cloud_session_cookie
        self.url = f"https://bitbucket.org/{self.workspace}"
        self.api = "https://api.bitbucket.org"
        self.session = self.set_session(self.username, self.password)
        # https://developer.atlassian.com/bitbucket/api/2/reference/resource/workspaces/%7Bworkspace%7D/permissions
        verify_api_endpoint = f'{self.api}/2.0/workspaces/{self.workspace}/permissions'
        self.verify_session(verify_api_endpoint, self.session)
        self.uuid = self._get_workspace_uuid()
    
    def _get_workspace_uuid(self) -> str:
        headers = {'Accept': 'application/json'}
        endpoint = f'{self.api}/2.0/workspaces/{self.workspace}'
        r = self.session.get(endpoint, headers=headers)
        r_json = r.json()
        return r_json.get('uuid')
