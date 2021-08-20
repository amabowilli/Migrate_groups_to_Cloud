from resources.instance_init import ServerInstance, CloudInstance
from resources.mirror_operations import ServerDetails as SD, ActionOnItems as AOI


def main() -> None:
    server = ServerInstance()
    cloud = CloudInstance()

    '''
    get list of groups_to_migrate to filter down to when mirroring the groups
    get all global groups and their perms to then be able to apply to resources/instance_actions.CloudActions.set_group_permissions
    get full layout of projects/repos so that we can flatten the permissions and apply the effective permission to a given group on a given repo
    '''

    groups_to_migrate, global_groups, server_structure = SD.scan_server_structure(server)
    print(groups_to_migrate)
    print()
    print(global_groups)
    print()
    print(server_structure)
    #AOI.mirror_groups(server, cloud, groups_to_migrate, global_groups)
    #AOI.mirror_repo_groups(server, cloud)


if __name__ == '__main__':
    main()
    exit()
