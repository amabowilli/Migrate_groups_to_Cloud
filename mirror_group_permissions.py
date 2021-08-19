from resources.groups import SeverGroups as sg, CloudGroups as cg
from resources.instances import ServerInstance, CloudInstance


def mirror_groups(server, cloud):
    group_memberships = 0
    group_counter = 0
    for group in sg.get_groups(server):
        group_counter += 1
        #cg.create_group(cloud, group)
        for member in sg.get_group_members(server, group):
            group_memberships += 1
            print(member.emailAddress)
            #cg.add_member_to_group(cloud, member, group)
    return group_memberships, group_counter

def mirror_repo_groups(server, cloud):
    pass



def main():
    server = ServerInstance()
    cloud = CloudInstance
    group_memberships, group_count = mirror_groups(server, cloud)
    print(f'Mirrored {group_count} groups with {group_memberships} group membership assignments')
    repo_count = mirror_repo_groups(server, cloud)
    print(f'Mirrored the groups/permissions for {repo_count} repositories.')
    exit()


if __name__ == '__main__':
    main()
