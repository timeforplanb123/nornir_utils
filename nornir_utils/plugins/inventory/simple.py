import logging
import pathlib
from typing import Any, Dict, Type

from nornir.core.inventory import (
    Inventory,
    Group,
    Groups,
    Host,
    Hosts,
    Defaults,
    ConnectionOptions,
    HostOrGroup,
    ParentGroups,
)

import ruamel.yaml

logger = logging.getLogger(__name__)


def get_connection_options(data: Dict[str, Any]) -> ConnectionOptions:
    cp = {}
    for cn, c in data.items():
        cp[cn] = ConnectionOptions(
            hostname=c.get("hostname"),
            port=c.get("port"),
            username=c.get("username"),
            password=c.get("password"),
            platform=c.get("platform"),
            extras=c.get("extras"),
        )
    return cp


def get_defaults(data: Dict[str, Any]) -> Defaults:
    return Defaults(
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        connection_options=get_connection_options(data.get("connection_options", {})),
    )


def get_inventory_element(
    typ: Type[HostOrGroup], data: Dict[str, Any], name: str, defaults: Defaults
) -> HostOrGroup:
    return typ(
        name=name,
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        groups=data.get(
            "groups"
        ),  # this is a hack, we will convert it later to the correct type
        defaults=defaults,
        connection_options=get_connection_options(data.get("connection_options", {})),
    )


class SimpleInventory(Inventory):
    def __init__(
        self,
        host_file: str = "hosts.yaml",
        group_file: str = "groups.yaml",
        defaults_file: str = "defaults.yaml",
    ) -> None:
        self.host_file = pathlib.Path(host_file)
        self.group_file = pathlib.Path(group_file)
        self.defaults_file = pathlib.Path(defaults_file)

    def load(self) -> Inventory:
        yml = ruamel.yaml.YAML(typ="safe")

        if self.defaults_file.exists():
            with open(self.defaults_file, "r") as f:
                defaults_dict = yml.load(f)
            defaults = get_defaults(defaults_dict)
        else:
            defaults = Defaults()

        hosts = Hosts()
        with open(self.host_file, "r") as f:
            hosts_dict = yml.load(f)

        for n, h in hosts_dict.items():
            hosts[n] = get_inventory_element(Host, h, n, defaults)

        groups = Groups()
        if self.group_file.exists():
            with open(self.group_file, "r") as f:
                groups_dict = yml.load(f)

            for n, g in groups_dict.items():
                groups[n] = get_inventory_element(Group, g, n, defaults)

            for h in hosts.values():
                h.groups = ParentGroups([groups[g] for g in h.groups])

            for g in groups.values():
                g.groups = ParentGroups([groups[g] for g in g.groups])

        return Inventory(hosts=hosts, groups=groups, defaults=defaults)