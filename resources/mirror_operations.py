from resources.instance_actions import Group, ServerActions as SA, CloudActions as CA
from resources.instance_init import ServerInstance, CloudInstance
from typing import Tuple

class ServerDetails:
    @staticmethod
    def scan_server_structure(server: ServerInstance) -> Tuple[list, dict, list]:
        groups_to_migrate = []
        global_groups = []
        for group in SA.get_group_global_permissions(server):
            global_groups.append(group)
            groups_to_migrate.append(group.name)

        used_groups, server_structure = ServerDetails.get_project_and_repo_structure(server)
        for group in used_groups:
            if group.name not in groups_to_migrate:
                groups_to_migrate.append(group.name)

        return groups_to_migrate, global_groups, server_structure

    @staticmethod
    def get_project_and_repo_structure(server: ServerInstance) -> Tuple[list[Group], list]:
        used_groups = []
        project_repo_structure = []
        ''' TODO
        Potentially speed up the script by multi-threading out each group and repo respectively
        as there's a lot of wasted time waiting for network responses (I/O).
        '''
        for project in SA.get_projects(server):
            for group in SA.get_project_groups(server, project):
                project.groups.append(group)
                if group.name not in used_groups:
                    used_groups.append(group)
            for repo in SA.get_repos(server, project):
                for group in SA.get_repo_groups(server, project, repo):
                    repo.groups.append(group)
                    if group.name not in used_groups:
                        used_groups.append(group)
                project.repositories.append(repo)
            project_repo_structure.append(project)

        return used_groups, project_repo_structure


class ActionOnItems:
    @staticmethod
    def mirror_groups(server: ServerInstance, cloud: CloudInstance, groups_to_migrate: list[str], global_groups: list[Group]) -> None:
        group_counter = 0
        group_memberships = 0
        
        for group_name in groups_to_migrate:
            if not CA.create_group(cloud, group_name):
                print(f'WARN: Failed to mirror group "{group_name}" to your cloud instance for unknown reason.')
                continue
            if not ActionOnItems.add_group_global_perms(cloud, group_name, global_groups):
                print(f'WARN: Failed to apply global permissions to {group_name} within your cloud instance.')
            group_migration = {'total_users': [], 'migrated_users': []}
            group_counter += 1
            for member in SA.get_group_members(server, group_name):
                group_migration['total_users'].append(member.emailAddress)
                if CA.add_member_to_group(cloud, group_name, member):
                    group_migration['migrated_users'].append(member.emailAddress)
                    group_memberships += 1

            if len(group_migration['total_users']) == len(group_migration['migrated_users']):
                print(f'INFO: Successfully migrated all {len(group_migration["total_users"])} users in group: {group_name}')
            else:
                print(f"WARN: Successfully migrated {len(group_migration['migrated_users'])} of {len(group_migration['total_users'])} members of {group_name}. Failed to mirror the following users to the group's membership:")
                print(', '.join([user_email for user_email in group_migration['total_users'] if user_email not in group_migration['migrated_users']]))

        print(f'INFO: Mirrored {group_counter} groups with {group_memberships} group membership assignments')

    @staticmethod
    def add_group_global_perms(cloud: CloudInstance, group_name: str, global_groups: list[Group]) -> bool:
        try:
            group = [group for group in global_groups if group.name == group_name][0]
        except IndexError:
            # the group_name doesn't have to be found within global_groups so simply skip if this is the case
            return True
        if group.permission == "LICENSED_USER":
            # do nothing as this is already implied by existing in the workspace
            return True
        elif group.permission == "PROJECT_CREATE":
            privilege = "None" # No default read/write/admin on any existing content
            account_privilege = "collaborator" # Can create new content though
        elif group.permission == "ADMIN":
            privilege = "Admin" # Admin on all existing content
            account_privilege = "collaborator" # Can create new content
        elif group.permission == "SYS_ADMIN":
            privilege = "Admin" # Admin on all existing content
            account_privilege = "admin" # Admin on workspace itself

        if CA.set_group_global_permissions(cloud, group.name, privilege, account_privilege):
            return True

        return False

    @staticmethod
    def max_permission(project_permission: str, repo_permission: str, repo_default: str) -> str:
        '''
        project_permission can be "None", "Read", "Write" or "Admin"
        repo_permission can be "None", "Read", "Write", or "Admin"
        repo_default can be "None", Read", or "Write"
        
        Determine the flattened/effective permission
        '''
        #TODO
        pass

    @staticmethod
    def mirror_repo_groups(server: ServerInstance, cloud: CloudInstance) -> None:
        #TODO
        repo_counter = 0

        print(f'INFO: Mirrored the groups/permissions for {repo_counter} repositories.')
