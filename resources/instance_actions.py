from resources.instance_init import ServerInstance, CloudInstance
from dataclasses import dataclass
from typing import Generator

@dataclass
class ServerUserData:
    name: str
    emailAddress: str
    displayName: str
    slug: str

class ServerActions(ServerInstance):

    def get_group_permissions(self, page=None, limit=1_000) -> Generator[str, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp63
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/admin/permissions/groups'
            r = self.session.get(endpoint, params=params, headers=headers)
            r_json = r.json()
            for group_data in r_json['values']:
                yield group_data.get('group').get('name'), group_data.get('permission')

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1
    
    def get_groups(self, page=None, limit=1_000) -> Generator[str, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp5
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/admin/groups'
            r = self.session.get(endpoint, params=params, headers=headers)
            r_json = r.json()
            for group_data in r_json['values']:
                yield group_data.get('name')

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1

    def get_group_members(self, group: str, page=None, limit=1_000) -> Generator[ServerUserData, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp11
        while True:
            headers = {'Accept': 'application/json'}
            params = {'context': group,'page': page, 'limit': limit}
            endpoint = f'{self.api}/admin/groups/more-members'
            r = self.session.get(endpoint, params=params, headers=headers)
            r_json = r.json()
            for user_data in r_json['values']:
                user = ServerUserData(user_data.get("name"), user_data.get("emailAddress"), user_data.get("displayName"), user_data.get("slug"))
                yield user

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1

    def get_projects(self, page=None, limit=1_000):
        pass

    def get_repos(self, project, page=None, limit=1_000):
        pass


class CloudActions(CloudInstance):

    def create_group(self, group: str) -> bool:
        # https://support.atlassian.com/bitbucket-cloud/docs/groups-endpoint/
        payload = f'name={group}'
        endpoint = f'{self.api}/1.0/groups/{self.workspace}'
        r = self.session.post(endpoint, data=payload)
        if r.status_code == 200:
            # Successfully created
            return True
        elif r.status_code == 400:
            # Already exists, return true to progress to assigning members
            return True
        else:
            return False

    def add_member_to_group(self, group: str, member: ServerUserData) -> bool:
        # https://support.atlassian.com/bitbucket-cloud/docs/groups-endpoint/
        headers = {'Content-type': 'application/json'}
        payload = '{}'
        endpoint = f'{self.api}/1.0/groups/{self.workspace}/{group}/members/{member.emailAddress}/'
        r = self.session.put(endpoint, headers=headers, data=payload)
        if r.status_code == 200:
            return True
        elif r.status_code == 409:
            # 409 is thrown if the user is already in the group
            return True
        else:
            # 404 is thrown if the user isn't within the workspace yet
            return False

    def add_group_to_repo(self, project, repo):
        pass
