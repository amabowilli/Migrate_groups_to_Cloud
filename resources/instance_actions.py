from resources.instance_init import ServerInstance, CloudInstance
from dataclasses import dataclass, field
from typing import Generator

@dataclass
class User:
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
    key: str
    name: str
    public: bool
    default_permission: str
    groups: list = field(default_factory=lambda: [])
    repositories: list = field(default_factory=lambda: [])

@dataclass
class Group:
    name: str
    permission: str = None

@dataclass
class Repository:
    slug: str
    name: str
    default_permission: str
    groups: list = field(default_factory=lambda: [])

class ServerActions(ServerInstance):

    def get_group_global_permissions(self, page=None, limit=1_000) -> Generator[GlobalGroup, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp63
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/admin/permissions/groups'
            r = self.get_api(endpoint, params=params, headers=headers)
            r_json = r.json()
            for group_data in r_json['values']:
                group = GlobalGroup(group_data.get('group').get('name'), group_data.get('permission'))
                yield group

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1
    
    def get_all_groups(self, page=None, limit=1_000) -> Generator[Group, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp5
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/admin/groups'
            r = self.get_api(endpoint, params=params, headers=headers)
            r_json = r.json()
            for group_data in r_json['values']:
                group = Group(group_data.get('name'))
                yield group

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1

    def get_group_members(self, group_name: str, page=None, limit=1_000) -> Generator[User, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp11
        while True:
            headers = {'Accept': 'application/json'}
            params = {'context': group_name,'page': page, 'limit': limit}
            endpoint = f'{self.api}/admin/groups/more-members'
            r = self.get_api(endpoint, params=params, headers=headers)
            r_json = r.json()
            for user_data in r_json['values']:
                user = User(user_data.get("name"), user_data.get("emailAddress"), user_data.get("displayName"), user_data.get("slug"))
                yield user

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1

    def get_projects(self, page=None, limit=1_000) -> Generator[Project, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp149
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/projects'
            r = self.get_api(endpoint, params=params, headers=headers)
            r_json = r.json()
            for project_data in r_json['values']:
                project_default_permission = ServerActions.get_project_default_permission(self, project_data)
                project = Project(project_data.get('key'), project_data.get('name'), project_data.get('public'), project_default_permission)
                yield project

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1
    
    def get_project_default_permission(self, project: dict) -> str:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp171
        headers = {'Accept': 'application/json'}
        endpoint = f'{self.api}/projects/{project.get("key")}/permissions/project_write/all'
        r = self.get_api(endpoint, headers=headers)
        r_json = r.json()
        if r_json.get('permitted') == True:
            default_permission = "Write"
        else:
            if project.get('public') == True:
                default_permission = "Read"
            else:
                endpoint = f'{self.api}/projects/{project.get("key")}/permissions/project_read/all'
                r = self.session.get(endpoint, headers=headers)
                r_json = r.json()
                if r_json.get('permitted') == True:
                    default_permission = "Read"
                else:
                    default_permission = "None"
        return default_permission

    def get_project_groups(self, project: Project, page=None, limit=1_000) -> Generator[Group, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp159
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/projects/{project.key}/permissions/groups'
            r = self.get_api(endpoint, params=params, headers=headers)
            r_json = r.json()
            for group_data in r_json['values']:
                group = Group(group_data.get('group').get('name'), group_data.get('permission'))
                yield group

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1

    def get_repos(self, project: Project, page=None, limit=1_000) -> Generator[Repository, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp175
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/projects/{project.key}/repos'
            r = self.get_api(endpoint, params=params, headers=headers)
            r_json = r.json()
            for repo_data in r_json['values']:
                if repo_data.get('public') == True:
                    repo_default_permission = "Read"
                else:
                    repo_default_permission = "None"
                repo = Repository(repo_data.get('slug'), repo_data.get('name'), repo_default_permission)
                yield repo
            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1

    def get_repo_groups(self, project: Project, repo: Repository, page=None, limit=1_000) -> Generator[Group, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp282
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/projects/{project.key}/repos/{repo.slug}/permissions/groups'
            r = self.get_api(endpoint, params=params, headers=headers)
            r_json = r.json()
            for group_data in r_json['values']:
                group = Group(group_data.get('group').get('name'), group_data.get('permission'))
                yield group

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1

class CloudActions(CloudInstance):

    def create_group(self, group_name: str) -> bool:
        # https://support.atlassian.com/bitbucket-cloud/docs/groups-endpoint/
        payload = f'name={group_name}'
        endpoint = f'{self.api}/1.0/groups/{self.workspace}'
        r = self.post_api(endpoint, payload)
        if r.status_code == 200:
            # Successfully created
            return True
        elif r.status_code == 400:
            # Already exists, return true to progress to assigning members
            return True
        else:
            return False

    def set_group_global_access(self, group_name: str, permission: str) -> bool:
        # https://support.atlassian.com/bitbucket-cloud/docs/groups-endpoint/
        '''
        sets default permission of group over all repos in workspace
        param: permission - can be "read", "write", or "admin"
        '''
        endpoint = f'{self.api}/1.0/groups/{self.workspace}/{group_name}/'
        payload = {'permission': permission}
        r = self.put_api(endpoint, payload, "json")
        if r.status_code == 200:
            return True
        return False

    def add_member_to_group(self, group: str, member: User) -> bool:
        # https://support.atlassian.com/bitbucket-cloud/docs/groups-endpoint/
        payload = '{}'
        endpoint = f'{self.api}/1.0/groups/{self.workspace}/{group}/members/{member.emailAddress}/'
        r = self.put_api(endpoint, payload, "data")
        if r.status_code == 200:
            return True
        elif r.status_code == 409:
            # 409 is thrown if the user is already in the group
            return True
        # 404 is thrown if the user isn't within the workspace yet
        return False

    def verify_repo_exists(self, repo_slug: str) -> bool:
        # https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Bworkspace%7D/%7Brepo_slug%7D#get
        endpoint = f'{self.api}/2.0/repositories/{self.workspace}/{repo_slug}'
        r = self.get_api(endpoint)
        if r.status_code == 200:
            return True
        return False

    def add_group_to_repo(self, repo_slug: str, group_name: str, flattened_permission: str) -> bool:
        # https://support.atlassian.com/bitbucket-cloud/docs/group-privileges-endpoint/
        payload = flattened_permission
        endpoint = f'{self.api}/1.0/group-privileges/{self.workspace}/{repo_slug}/{self.workspace}/{group_name}'
        r = self.put_api(endpoint, payload, "data")
        if r.status_code == 200:
            return True
        return False
