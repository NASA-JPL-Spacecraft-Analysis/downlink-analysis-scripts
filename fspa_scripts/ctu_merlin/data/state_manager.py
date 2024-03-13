"""Interacting with State Manager data"""

from typing import List
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class SMState:
    identifier: str
    displayName: str = field(default_factory=lambda: "")
    dataType: str = field(default_factory=lambda: "")
    type: str = field(default_factory=lambda: "predict")
    units: str = field(default_factory=lambda: "")
    source: str = field(default_factory=lambda: "clipper-merlin")
    subsystem: str = field(default_factory=lambda: "")
    channelId: str = field(default_factory=lambda: "")
    restricted: bool = False
    description: str = field(default_factory=lambda: "")
    externalLink: str = field(default_factory=lambda: "")
    version: str = field(default_factory=lambda: "")

    def __post_init__(self):
        if self.displayName == "":
            self.displayName = self.identifier


@dataclass_json
@dataclass
class SMStateEnumeration:
    stateIdentifier: str
    label: str
    value: str


@dataclass_json
@dataclass
class GroupMapping:
    itemIdentifier: str
    itemType: str
    sortOrder: int


@dataclass_json
@dataclass
class SMGroup:
    identifier: str
    groupMappings: List[GroupMapping]
