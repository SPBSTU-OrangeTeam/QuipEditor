class ChatView:

    def __init__(self, id=None, view=None):
        self.id = id
        self.view = view
        self.phantoms = []
        self.name = "Private chat"

    def add_phantom(self, phantom):
        self.phantoms.extend([phantom, phantom])