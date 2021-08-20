from resources.instance_init import ServerInstance, CloudInstance
from resources.mirror_operations import mirror_groups, mirror_repo_groups


def main() -> None:
    server = ServerInstance()
    cloud = CloudInstance()
    mirror_groups(server, cloud)
    mirror_repo_groups(server, cloud)


if __name__ == '__main__':
    main()
    exit()
