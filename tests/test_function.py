"""
title: Test Function
author: Backend Team
version: 1.0.0
description: Minimal test function for OpenWebUI
"""

class Valves:
    def __init__(self):
        self.debug_mode = True

class Function:
    def __init__(self):
        self.valves = Valves()

    def pipe(self, user_message, model_id, messages, body):
        print("[Test Function] Working!")
        return user_message
