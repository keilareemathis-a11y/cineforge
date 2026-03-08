class Settings:
    def __init__(self, app_name: str, debug: bool = False, version: str = "1.0.0"):
        self.app_name = app_name
        self.debug = debug
        self.version = version

    @property
    def description(self) -> str:
        return f"{self.app_name} - Version: {self.version}"

    @property
    def is_debug_mode(self) -> bool:
        return self.debug
