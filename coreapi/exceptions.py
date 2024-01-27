class WebSocketClosedByClient(Exception):
    """Exception raised when the WebSocket connection is closed by client"""

    def __init__(self, message="WebSocket connection closed by client"):
        self.message = message
        super().__init__(self.message)
