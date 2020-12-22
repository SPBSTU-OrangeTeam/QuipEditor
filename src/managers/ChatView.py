class ChatView:

    def __init__(self):
        self.view = None
        self.phantoms = []
        self.id = None
        self.name = "Private chat"

    def add_phantom(self, phantom):
        self.phantoms.append(phantom)