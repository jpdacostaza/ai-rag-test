"""
Simple test pipeline for debugging
"""

class Pipeline:
    def __init__(self):
        self.name = "test_debug_pipeline"
        print(f"🔧 DEBUG: {self.name} initialized!")
    
    def inlet(self, body, user=None):
        """Process incoming messages"""
        print(f"🔧 DEBUG: inlet called with body: {str(body)[:200]}...")
        print(f"🔧 DEBUG: user: {user}")
        return body
    
    def outlet(self, body, user=None):
        """Process outgoing messages"""
        print(f"🔧 DEBUG: outlet called")
        return body
