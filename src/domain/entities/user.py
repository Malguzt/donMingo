class User:
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email
    
    def __eq__(self, other):
        return self.email == other.email
    
    def __hash__(self):
        return hash(self.email)