#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# (c) Andreas Doehler <andreas.doehler@bechtle.com/andreas.doehler@gmail.com>

# License: GNU General Public License v2

from cmk.agent_based.v2 import AgentSection, CheckPlugin, Result, Service, State
from cmk.agent_based.v2.type_defs import CheckResult, DiscoveryResult
from cmk.plugins.redfish.lib import (
    RedfishAPIData,
    parse_redfish_multiple,
    redfish_health_state,
)

agent_section_redfish_processors = AgentSection(
    name="redfish_processors",
    parse_function=parse_redfish_multiple,
    parsed_section_name="redfish_processors",
)


def discovery_redfish_processors(section: RedfishAPIData) -> DiscoveryResult:
    """Discover single present CPUs"""
    for key in section.keys():
        if section[key].get("Status", {}).get("State") == "Absent":
            continue
        yield Service(item=section[key]["Id"])


def check_redfish_processors(item: str, section: RedfishAPIData) -> CheckResult:
    """Check state of CPU"""
    data = section.get(item, None)
    if data is None:
        return

    if data.get("Model") == "Undefined":
        cpu_model = data.get("ProcessorId", {}).get("EffectiveFamily")
    else:
        cpu_model = data.get("Model")
    cpu_msg = f"Type: {data.get('ProcessorType')}, Model: {cpu_model}"

    if "TotalCores" in data.keys():
        if data.get("OperatingSpeedMHz"):
            cpu_speed = data.get("OperatingSpeedMHz")
        else:
            cpu_speed = "maximum " + str(data.get("MaxSpeedMHz"))
        cpu_msg = (
            f"{cpu_msg}, Cores: {data.get('TotalCores')}, "
            f"Threads: {data.get('TotalThreads')}, Speed {cpu_speed} MHz"
        )
    yield Result(state=State(0), summary=cpu_msg)

    dev_state, dev_msg = redfish_health_state(data["Status"])

    yield Result(state=State(dev_state), notice=dev_msg)


check_plugin_redfish_processors = CheckPlugin(
    name="redfish_processors",
    service_name="CPU %s",
    sections=["redfish_processors"],
    discovery_function=discovery_redfish_processors,
    check_function=check_redfish_processors,
)
