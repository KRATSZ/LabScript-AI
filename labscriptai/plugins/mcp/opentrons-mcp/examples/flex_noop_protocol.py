from opentrons import protocol_api

metadata = {
    "protocolName": "Flex Noop Validation",
    "author": "Cursor",
    "description": "Low-risk protocol used to validate upload/create/play/poll MCP flow.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.22"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    protocol.comment("noop validation start")
    protocol.comment("noop validation end")
