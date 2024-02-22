from typing import Dict
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class CSDSState:
    # TODO check field types. Parse times? Make all kw_only with defaults?
    # id: str = field(default_factory=lambda: "")
    collectionName: str = field(default_factory=lambda: "")
    name: str = field(default_factory=lambda: "")
    sessionId: str = field(default_factory=lambda: "")
    planId: str = field(default_factory=lambda: "")
    runId: str = field(default_factory=lambda: "")
    scet: str = field(default_factory=lambda: "")
    scetEnd: str = field(default_factory=lambda: "")
    ert: str = field(default_factory=lambda: "")
    type: str = field(default_factory=lambda: "")
    value: float = field(default_factory=lambda: -99999) # TODO only floats are allowed? Resolve for other data.
    metadata: Dict = field(default_factory=lambda: {})
    # cpu: str = field(default_factory=lambda: "")
    # hexId: str = field(default_factory=lambda: "")
    valueType: str = field(default_factory=lambda: "PREDICTED")
    # version: str = field(default_factory=lambda: "")
    # volatility: str = field(default_factory=lambda: "NON_VOLATILE") # TODO Merlin integration probably shouldn't specify a volatility
