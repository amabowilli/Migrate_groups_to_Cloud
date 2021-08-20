from resources.instance_init import ServerInstance, CloudInstance
from dataclasses import dataclass
from typing import Generator

@dataclass
class ServerUserData:
    name: str
    emailAddress: str
    displayName: str
    slug: str

@dataclass
class GlobalGroup:
    name: str
    permission: str

@dataclass
class Project:
    name: str
    default_permission: str
    groups: list = []
    repositories: list = []

@dataclass
class Group:
    name: str
    permission: str = None

@dataclass
class Repository:
    name: str
    default_permission: str
    groups: list = []

class ServerActions(ServerInstance):

    def get_group_global_permissions(self, page=None, limit=1_000) -> Generator[GlobalGroup, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp63
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/admin/permissions/groups'
            r = self.session.get(endpoint, params=params, headers=headers)
            r_json = r.json()
            for group_data in r_json['values']:
                group = GlobalGroup(group_data.get('group').get('name'), group_data.get('permission'))
                yield group

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1
    
    def get_groups(self, page=None, limit=1_000) -> Generator[Group, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp5
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/admin/groups'
            r = self.session.get(endpoint, params=params, headers=headers)
            r_json = r.json()
            for group_data in r_json['values']:
                group = Group(group_data.get('name'))
                yield group

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

    def set_group_permissions(self, group: str, privilege: str, account_privilege: str) -> bool:
        '''
        param privilege: can be "None", "Read", "Write", or "Admin". Applies the given default permission to all repos within the workspace
        param account_privilege: can be "None", "collaborator", or "admin". Enables the checkboxes for "Create Repositories" and "Administer workspace" respectively
        '''
        # sourced from web broswer devpanel, no public API available
        endpoint = f"https://bitbucket.org/api/internal/workspaces/{self.workspace}/groups/{group}"
        headers = {"Accept": "application/json", "Content-type": "application/json"}
        payload = {"name": group, "privilege": privilege, "account_privilege": account_privilege}
        r = self.session.put(endpoint, headers=headers, data=payload)
        if r.status_code == 200:
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

    def add_group_to_repo(self, project: str, repo: str) -> bool:
        pass
