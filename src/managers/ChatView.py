class ChatView:

    def __init__(self):
        self.view = None
        self.phantoms = []
        self.chat_id = None
        self.chat_name = "Private chat"

    def add_phantom(self, phantom):
        self.phantoms.append(phantom)