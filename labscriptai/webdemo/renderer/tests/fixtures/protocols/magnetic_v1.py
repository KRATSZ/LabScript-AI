"""Magnetic GEN1 fixture using the same valid slot and volume as V2."""

from opentrons import protocol_api

metadata = {"protocolName": "OT-2 fixture: magnetic module V1"}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_300ul", "1", "300 uL tips")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "2", "source reservoir")
    magnetic = ctx.load_module("magneticModuleV1", "6")
    plate = magnetic.load_labware("nest_96_wellplate_200ul_flat")
    p300 = ctx.load_instrument("p300_single_gen2", "right", tip_racks=[tips])

    water = ctx.define_liquid("Water", "magnetic V1 source", "#4EA5D9")
    reservoir["A1"].load_liquid(water, 500)
    p300.pick_up_tip(tips["A1"])
    p300.aspirate(40, reservoir["A1"].bottom(1))
    p300.dispense(40, plate["A1"].bottom(1))
    magnetic.engage(height_from_base=10)
    ctx.delay(seconds=1)
    magnetic.disengage()
    p300.drop_tip()
