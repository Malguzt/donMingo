class User:
    def __init__(self, platform_id: int, platform: str, name: str = ""):
        if not platform_id:
            raise ValueError("Platform ID is required")
        if not platform:
            raise ValueError("Platform is required")
        self.platform_id = platform_id
        self.platform = platform
        self.name = name
    
    def __eq__(self, other):
        return self.platform_id == other.platform_id and self.platform == other.platform
    
    def __hash__(self):
        return hash((self.platform_id, self.platform))