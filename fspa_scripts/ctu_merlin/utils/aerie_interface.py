from dataclasses_json import dataclass_json, config
from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import timedelta
import arrow

from aerie_cli.aerie_client import AerieClient as AC_Base
from aerie_cli.utils.serialization import postgres_interval_to_timedelta, timedelta_to_postgres_interval

from fspa_scripts.ctu_merlin.data.merlin import ValueSchema


@dataclass_json
@dataclass
class ProfileType:
    type: str
    schema: ValueSchema = field(
        metadata=config(
            decoder=ValueSchema.parse_unknown_schema,
            encoder=ValueSchema.unknown_to_schema
        )
    )


@dataclass_json
@dataclass
class ProfileSegment:
    dynamics: Any
    start_offset: timedelta = field(
        metadata=config(
            decoder=postgres_interval_to_timedelta,
            encoder=timedelta_to_postgres_interval
        )
    )


@dataclass_json
@dataclass
class ResourceProfile:
    name: str
    profile_segments: List[ProfileSegment]
    type: ProfileType


class CTUAerieClient(AC_Base):
    def get_resource_profile(self, resource_name: str, simulation_dataset_id: int) -> ResourceProfile:
        """Get the resource profile (all segments) for a given resource name
        """

        resource_profile_query = """
        query GetResourceProfile($simulation_dataset_id: Int!, $resource_name: String!) {
            simulation_dataset_by_pk(id: $simulation_dataset_id) {
                dataset {
                    profiles(where: {name: {_eq: $resource_name}}) {
                        name
                        profile_segments(order_by: {start_offset: desc}) {
                            dynamics
                            start_offset
                        }
                        type
                    }
                }
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(
            resource_profile_query,
            simulation_dataset_id=simulation_dataset_id,
            resource_name=resource_name
        )

        if not len(resp["dataset"]["profiles"]):
            raise RuntimeError("No resource profile found")

        return ResourceProfile.from_dict(resp["dataset"]["profiles"][0])

    def get_resource_names(self, simulation_dataset_id: int) -> List[str]:
        resource_names_query = """
        query GetResourceNames($simulation_dataset_id: Int!) {
            simulation_dataset_by_pk(id: $simulation_dataset_id) {
                dataset {
                    profiles {
                        name
                    }
                }
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(
            resource_names_query,
            simulation_dataset_id=simulation_dataset_id
        )

        return [p["name"] for p in resp["dataset"]["profiles"]]

    def get_simulation_start_time(self, simulation_dataset_id: int) -> arrow.Arrow:
        query = """
        query MyQuery($simulation_dataset_id: Int!) {
            simulation_dataset_by_pk(id: $simulation_dataset_id) {
                simulation_start_time
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            query,
            simulation_dataset_id=simulation_dataset_id
        )
        if "simulation_start_time" not in resp.keys():
            raise RuntimeError(
                f"No simulation dataset with ID: {simulation_dataset_id}")

        return arrow.get(resp["simulation_start_time"])
