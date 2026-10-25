"""Temperature GEN1 fixture using the same valid slot and volume as V2."""

from opentrons import protocol_api

metadata = {"protocolName": "OT-2 fixture: temperature module V1"}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_300ul", "1", "300 uL tips")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "2", "source reservoir")
    temperature = ctx.load_module("temperatureModuleV1", "6")
    plate = temperature.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    p300 = ctx.load_instrument("p300_single_gen2", "right", tip_racks=[tips])

    water = ctx.define_liquid("Water", "temperature V1 source", "#4EA5D9")
    reservoir["A1"].load_liquid(water, 500)
    p300.pick_up_tip(tips["A1"])
    p300.aspirate(30, reservoir["A1"].bottom(1))
    p300.dispense(30, plate["A1"].bottom(1))
    temperature.set_temperature(celsius=55)
    ctx.delay(seconds=2)
    temperature.deactivate()
    p300.drop_tip()
