from resources.instance_actions import ServerActions as SA, CloudActions as CA


def mirror_groups(server, cloud):
    group_counter = 0
    group_memberships = 0
    
    for group in SA.get_groups(server):
        if not CA.create_group(cloud, group):
            print(f'WARN: Failed to mirror group "{group}" to your cloud instance')
            continue
        group_migration = {'total_users': [], 'migrated_users': []}
        group_counter += 1
        for member in SA.get_group_members(server, group):
            group_migration['total_users'].append(member.emailAddress)
            if CA.add_member_to_group(cloud, group, member):
                group_migration['migrated_users'].append(member.emailAddress)
                group_memberships += 1

        if len(group_migration['total_users']) == len(group_migration['migrated_users']):
            print(f'INFO: Successfully migrated all {len(group_migration["total_users"])} users in group: {group}')
        else:
            print(f"WARN: Successfully migrated {len(group_migration['migrated_users'])} of {len(group_migration['total_users'])} members of {group}. Failed to mirror the following users to the group's membership:")
            print(', '.join([user_email for user_email in group_migration['total_users'] if user_email not in group_migration['migrated_users']]))


    print(f'INFO: Mirrored {group_counter} groups with {group_memberships} group membership assignments')


def mirror_repo_groups(server, cloud):
    repo_counter = 0
    print(f'INFO: Mirrored the groups/permissions for {repo_counter} repositories.')
