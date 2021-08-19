from resources.instances import ServerInstance, CloudInstance
from dataclasses import dataclass
from typing import Generator

@dataclass
class ServerUserData:
    name: str
    emailAddress: str
    displayName: str
    slug: str

class SeverGroups(ServerInstance):
    
    def get_groups(self, page=None, limit=1_000) -> Generator[str, None, None]:
        while True:
            headers = {'Accept': 'application/json'}
            params = {'page': page, 'limit': limit}
            r = self.session.get(f'{self.api}/admin/groups', params=params, headers=headers)
            r_json = r.json()
            for group_data in r_json['values']:
                yield group_data.get('name')

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1

    def get_group_members(self, group, page=None, limit=1_000) -> Generator[ServerUserData, None, None]:
        while True:
            headers = {'Accept': 'application/json'}
            params = {'context': group,'page': page, 'limit': limit}
            r = self.session.get(f'{self.api}/admin/groups/more-members', params=params, headers=headers)
            r_json = r.json()
            for user_data in r_json['values']:
                user = ServerUserData(user_data.get("name"), user_data.get("emailAddress"), user_data.get("displayName"), user_data.get("slug"))
                yield user

            if not r_json.get('nextPageStart'):
                return
            
            if page == None:
                page = 1
            page += 1

class CloudGroups(CloudInstance):

    def create_group(self, group):
        pass

    def add_member_to_group(self, group):
        pass