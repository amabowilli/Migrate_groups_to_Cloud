class InstanceNotAvailable(Exception):
    def __init__(self, msg) -> None:
        super().__init__(msg)


