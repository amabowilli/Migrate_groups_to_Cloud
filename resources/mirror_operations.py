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
    def mirror_groups(server: ServerInstance, cloud: CloudInstance, groups_to_migrate: list[str], global_groups: list[Group]) -> dict:
        group_counter = 0
        group_memberships = 0
        group_workspace_privileges = {'create_repositories': [], 'admin_workspace': []}

        for group_name in groups_to_migrate:
            if not CA.create_group(cloud, group_name):
                print(f'WARN: Failed to mirror group "{group_name}" to your cloud instance for unknown reason.')
                continue
            success, permission = ActionOnItems.add_group_global_perms(cloud, group_name, global_groups)
            if not success:
                print(f'WARN: Failed to apply global permissions to {group_name} within your cloud instance.')
            if permission == "create_repositories":
                group_workspace_privileges.get('create_repositories').append(group_name)
            elif permission == "admin_workspace":
                group_workspace_privileges.get('admin_workspace').append(group_name)
            #if not ActionOnItems.add_group_global_perms(cloud, group_name, global_groups):
            #    print(f'WARN: Failed to apply global permissions to {group_name} within your cloud instance.')
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
        return group_workspace_privileges

    @staticmethod
    def add_group_global_perms(cloud: CloudInstance, group_name: str, global_groups: list[Group]) -> tuple[bool, str]:
        try:
            group = [group for group in global_groups if group.name == group_name][0]
        except IndexError:
            # the group_name doesn't have to be found within global_groups so simply skip if this is the case
            return True, None

        if group.permission == "LICENSED_USER":
            # do nothing as this is already implied by existing in the workspace
            return True, None
        elif group.permission == "PROJECT_CREATE":
            # No default read/write/admin on any existing content
            return True, "create_repositories"
        elif group.permission == "ADMIN":
            return CA.set_group_global_access(cloud, group.name, "admin"), "create_repositories"
        elif group.permission == "SYS_ADMIN":
            return CA.set_group_global_access(cloud, group.name, "admin"), "admin_workspace"

        return False, None

    @staticmethod
    def mirror_repo_groups(server: ServerInstance, cloud: CloudInstance, groups_to_migrate: list[str], server_structure: list[Project]) -> None:
        successful_repo_counter = 0
        total_repo_counter = 0
        for project in server_structure:
            repo: Repository
            for repo in project.repositories:
                if not CA.verify_repo_exists(cloud, repo.slug):
                    print(f'INFO: Skipping repo "{repo.name}" as it is not present within your cloud workspace. This may not have been migrated yet.')
                    continue
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

    @staticmethod
    def print_group_privilege_details(group_workspace_privileges: dict, workspace_name: str) -> None:
        print("\n\nThe following groups had a level of permission within Bitbucket Server that the API does not allow this script to mirror.\n"
              f"We recommend going to your workspace group settings page, Found at: https://bitbucket.org/{workspace_name}/workspace/settings/groups, to add the following settings:")
        
        print('\n----- "Create Repositories" -----')
        print(', '.join(group_workspace_privileges.get('create_repositories')))

        print('\n----- "Administer Workspace" ----- (automatically inherits the "Create Repositories" permission)')
        print(', '.join(group_workspace_privileges.get('admin_workspace')))
