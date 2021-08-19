from resources.instances import ServerInstance, CloudInstance

class ServerRepos(ServerInstance):
    def get_projects(self, page=None, limit=1_000):
        pass

    def get_repos(self, project, page=None, limit=1_000):
        pass

class CloudRepos(CloudInstance):
    def add_group_to_repo(self, project, repo):
        pass

