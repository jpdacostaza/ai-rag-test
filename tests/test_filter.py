"""
title: Test Filter
author: Backend Team
version: 1.0.0
description: Test filter for OpenWebUI
"""

class Valves:
    def __init__(self):
        self.debug_mode = True

class Filter:
    def __init__(self):
        self.valves = Valves()

    def inlet(self, body: dict, user: dict = None) -> dict:
        print("[Test Filter] Inlet processing")
        return body

    def outlet(self, body: dict, user: dict = None) -> dict:
        print("[Test Filter] Outlet processing")
        return body
