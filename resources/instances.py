from requests import Session
from requests.exceptions import SSLError
import env


class InstanceNotAvailable(Exception):
    def __init__(self, msg) -> None:
        super().__init__(msg)

class Instance():
    def __init__():
        pass

    @staticmethod
    def set_session(username, password):
        session = Session()
        session.auth = (username, password)
        return session

    @staticmethod
    def verify_session(api_url, session):
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
        self.verify_url()
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp45
        verify_api_endpoint = f'{self.api}/admin/cluster'
        self.verify_session(verify_api_endpoint, self.session)

    def verify_url(self):
        try:
            r = self.session.get(f'{self.url}/status')
            self.verify = True #Using https and ssl cert is good
        except SSLError:
            self.verify = False # Using https and ssl cert is self-signed or other issue, ignorable
            r = self.session.get(f'{self.url}/status', verify=self.verify)

        if not "RUNNING" in r.text:
            raise InstanceNotAvailable(f'Did not get a "RUNNING" response from the url "{self.url}/status"')


class CloudInstance(Instance):
    def __init__(self):
        self.username = env.cloud_username
        self.password = env.cloud_password
        self.workspace = env.cloud_workspace
        self.url = f"https://bitbucket.org/{self.workspace}"
        self.api = "https://api.bitbucket.org"
        self.session = self.set_session(self.username, self.password)
        # https://developer.atlassian.com/bitbucket/api/2/reference/resource/workspaces/%7Bworkspace%7D/permissions
        verify_api_endpoint = f'{self.api}/2.0/workspaces/{self.workspace}/permissions'
        self.verify_session(verify_api_endpoint, self.session)

