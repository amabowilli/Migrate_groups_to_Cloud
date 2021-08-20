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
    
    def get_all_groups(self, page=None, limit=1_000) -> Generator[Group, None, None]:
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

    def get_group_members(self, group: Group, page=None, limit=1_000) -> Generator[User, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp11
        while True:
            headers = {'Accept': 'application/json'}
            params = {'context': group.name,'page': page, 'limit': limit}
            endpoint = f'{self.api}/admin/groups/more-members'
            r = self.session.get(endpoint, params=params, headers=headers)
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
            r = self.session.get(endpoint, params=params, headers=headers)
            r_json = r.json()
            for project_data in r_json['values']:
                project_default_permission = ServerActions.get_project_default_permission(self, project_data.get('key'))
                project = Project(project_data.get('key'), project_data.get('name'), project_default_permission)
                yield project

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1
    
    def get_project_default_permission(self, project_key: str) -> str:
        #TODO Get project specific default permission https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp171
        return "None"

    def get_project_groups(self, project: Project, page=None, limit=1_000) -> Generator[Group, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp159
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/projects/{project.key}/permissions/groups'
            r = self.session.get(endpoint, params=params, headers=headers)
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
            r = self.session.get(endpoint, params=params, headers=headers)
            r_json = r.json()
            for repo_data in r_json['values']:
                repo_default_permission = ServerActions.get_repo_default_permission(self, project.key, repo_data.get('slug'))
                project = Project(repo_data.get('slug'), repo_data.get('name'), repo_default_permission)
                yield project

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1

    def get_repo_default_permission(self, project_key: str, repo_slug: str) -> str:
        #TODO Get repo specific default permission
        return "None"

    def get_repo_groups(self, project: Project, repo: Repository, page=None, limit=1_000) -> Generator[Group, None, None]:
        # https://docs.atlassian.com/bitbucket-server/rest/7.15.1/bitbucket-rest.html#idp282
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            endpoint = f'{self.api}/projects/{project.key}/repos/{repo.slug}/permissions/groups'
            r = self.session.get(endpoint, params=params, headers=headers)
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

    def add_member_to_group(self, group: str, member: User) -> bool:
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
