#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# (c) Andreas Doehler <andreas.doehler@bechtle.com/andreas.doehler@gmail.com>

# License: GNU General Public License v2

from cmk.agent_based.v2 import AgentSection, CheckPlugin, Metric, Result, Service, State
from cmk.agent_based.v2.type_defs import CheckResult, DiscoveryResult
from cmk.plugins.redfish.lib import (
    RedfishAPIData,
    parse_redfish_multiple,
    redfish_health_state,
)

agent_section_redfish_physicaldrives = AgentSection(
    name="redfish_physicaldrives",
    parse_function=parse_redfish_multiple,
    parsed_section_name="redfish_physicaldrives",
)


def discovery_redfish_physicaldrives(section: RedfishAPIData) -> DiscoveryResult:
    for key in section.keys():
        loc = section[key].get("Location")
        if loc == []:
            item = section[key]["Name"]
        else:
            item = section[key]["Location"]

        yield Service(item=item)


def check_redfish_physicaldrives(item: str, section: RedfishAPIData) -> CheckResult:
    data = None
    for key in section.keys():
        if item == section[key].get("Location"):
            data = section.get(key, None)
        elif item == section[key].get("Name"):
            data = section.get(key, None)
    if data is None:
        return

    capacity = data.get("CapacityBytes", None)
    if not capacity:
        capacity = data.get("CapacityMiB", None)
        if capacity:
            capacity = capacity / 1024
    else:
        capacity = capacity / 1024 / 1024 / 1024

    speed = data.get("CapableSpeedGbs", None)
    if not speed:
        speed = data.get("InterfaceSpeedMbps", 0)
        speed = speed / 1000

    disc_msg = f"Size: {capacity:0.0f}GB, Speed {speed} Gbs"

    if data.get("MediaType") == "SSD":
        if data.get("PredictedMediaLifeLeftPercent"):
            disc_msg = (
                f"{disc_msg}, Media Life Left: "
                f"{int(data.get('PredictedMediaLifeLeftPercent', 0))}%"
            )
        elif data.get("SSDEnduranceUtilizationPercentage"):
            disc_msg = (
                f"{disc_msg}, SSD Utilization: "
                f"{int(data.get('SSDEnduranceUtilizationPercentage', 0))}%"
            )
    yield Result(state=State(0), summary=disc_msg)

    dev_state, dev_msg = redfish_health_state(data["Status"])
    status = dev_state
    message = dev_msg
    yield Result(state=State(status), notice=message)

    dev_ser = data.get("SerialNumber")
    dev_mod = data.get("Model")
    yield Result(state=State(0), notice=f"Serial: {dev_ser}\nModel: {dev_mod}")

    if data.get("CurrentTemperatureCelsius", None):
        yield Metric("temp", int(data.get("CurrentTemperatureCelsius")))


check_plugin_redfish_physicaldrives = CheckPlugin(
    name="redfish_physicaldrives",
    service_name="Drive %s",
    sections=["redfish_physicaldrives"],
    discovery_function=discovery_redfish_physicaldrives,
    check_function=check_redfish_physicaldrives,
)
