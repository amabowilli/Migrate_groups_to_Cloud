from resources.instance_actions import Group, Project, Repository, ServerActions as SA, CloudActions as CA
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
                print('-'*10)
                print(', '.join([user_email for user_email in group_migration['total_users'] if user_email not in group_migration['migrated_users']]))
                print('-'*10)

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
            privilege = "none" # No default read/write/admin on any existing content
            account_privilege = "collaborator" # Can create new content though
        elif group.permission == "ADMIN":
            privilege = "admin" # Admin on all existing content
            account_privilege = "collaborator" # Can create new content
        elif group.permission == "SYS_ADMIN":
            privilege = "admin" # Admin on all existing content
            account_privilege = "admin" # Admin on workspace itself

        if CA.set_group_global_permissions(cloud, group.name, privilege, account_privilege):
            return True

        return False

    @staticmethod
    def mirror_repo_groups(server: ServerInstance, cloud: CloudInstance, groups_to_migrate: list[str], server_structure: list[Project]) -> None:
        successful_repo_counter = 0
        total_repo_counter = 0
        for project in server_structure:
            repo: Repository
            for repo in project.repositories:
                print(f'INFO: Mirroring group permissions for repo: "{repo.name}"')
                atleast_one_group_migrated = False
                for group_name, flattened_permission in ActionOnItems.max_permission(project.default_permission, project.groups, repo.default_permission, repo.groups, groups_to_migrate):
                    if flattened_permission == "none":
                        continue
                    if CA.add_group_to_repo(cloud, repo.slug, group_name, flattened_permission):
                        atleast_one_group_migrated = True
                    else:
                        print(f'WARN: Failed to add group "{group_name}" with permission "{flattened_permission}" to "{repo.name}".')
                if atleast_one_group_migrated:
                    successful_repo_counter += 1
                total_repo_counter += 1
        print(f'INFO: Successfully mirrored the groups/permissions for {successful_repo_counter} of {total_repo_counter} repositories.')

    @staticmethod
    def max_permission(project_default_permission: str, project_groups: list[Group], repo_default_permission: str, repo_groups: list[Group], groups_to_migrate: list[str]) -> str:
        '''
        project_default can be "None", "Read", or "Write"
        project_permission can be "None", "Read", "Write" or "Admin"
        repo_permission can be "None", "Read", "Write", or "Admin"
        repo_default can be "None" or "Read" (public checkbox)
        
        Determine/return the flattened/effective permission
        '''
        for group_name in groups_to_migrate:
            group_project_perm = ActionOnItems.lookup_group_perm(group_name, project_groups)
            group_repo_perm = ActionOnItems.lookup_group_perm(group_name, repo_groups)
            perms = [project_default_permission, group_project_perm, repo_default_permission, group_repo_perm]
            if "Admin" in perms:
                yield group_name, "admin"
            elif "Write" in perms:
                yield group_name, "write"
            elif "Read" in perms:
                yield group_name, "read"
            else:
                yield group_name, "none"

    @staticmethod
    def lookup_group_perm(group_name: str, groups: list[Group]) -> str:
        permission = "None"
        for group in groups:
            if group.name == group_name:
                permission = group.permission
                break

        if permission in ["PROJECT_ADMIN", "REPO_ADMIN"]:
            permission = "Admin"
        elif permission in ["PROJECT_WRITE", "REPO_WRITE"]:
            permission = "Write"
        elif permission in ["PROJECT_READ", "REPO_READ"]:
            permission = "Read"
        return permission
