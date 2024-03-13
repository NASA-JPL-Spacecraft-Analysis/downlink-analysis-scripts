"""Clipper Merlin State Javadocs

Dataclasses describe the structure of the Javadoc states containing annotations for Clipper Merlin states.
"""

from typing import Dict


class JavadocState:
    def __init__(
        self,
        resource: str = None,
        units: str = None,
        docs: str = None
    ) -> None:
        self.resource = resource if resource else ""
        self.units = units if units else ""
        self.docs = docs if docs else ""
