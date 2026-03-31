import math

metadata = {
    'protocolName': 'Peptide Mass Spec Sample Prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [samples, m20_mount, m300_mount, mag_engage_height, bead_vol, asp_speed,
        mecn_wash1_vol, mecn_wash2_vol, mecn_wash3_vol,
        supernat_1_vol, supernat_2_vol, supernat_3_vol,
        elution_buff_vol, peptide_supernat_vol, formic_acid_vol,
        irt_vol] = get_values(  # noqa: F821
        "samples", "m20_mount", "m300_mount", "mag_engage_height", "bead_vol",
        "asp_speed", "mecn_wash1_vol", "mecn_wash2_vol",
        "mecn_wash3_vol", "supernat_1_vol", "supernat_2_vol",
        "supernat_3_vol", "elution_buff_vol", "peptide_supernat_vol",
        "formic_acid_vol", "irt_vol")

    if not 1 <= samples <= 48:
        raise Exception("Enter a sample number between 1 and 48.")

    columns = math.ceil(samples/8)

    # Load Modules
    mag_mod = ctx.load_module("magnetic module gen2", 4)
    dwp = mag_mod.load_labware("stellarscientific_96_cluster_tubes_1200ul")

    # Load Labware
    tiprack_300 = [ctx.load_labware("opentrons_96_tiprack_300ul",
                                    slot) for slot in [5, 8]]
    tiprack_20 = [ctx.load_labware("opentrons_96_tiprack_20ul",
                                   slot) for slot in [6, 9]]
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", 3)
    nunc_96v = ctx.load_labware("nunc_v96_microwell_plate", 1)
    pcr_plate = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 2)
    trash = ctx.loaded_labwares[12]['A1']

    # Load Pipettes
    m20 = ctx.load_instrument("p20_multi_gen2", m20_mount,
                              tip_racks=tiprack_20)
    m300 = ctx.load_instrument("p300_multi_gen2", m300_mount,
                               tip_racks=tiprack_300)

    # Reagents
    sp2_beads = nunc_96v['A1']
    elution_buffer = nunc_96v['A2']
    formic_acid = nunc_96v['A3']
    irt = nunc_96v['A4']
    mecn_set1 = reservoir.rows()[0][0::2][:columns]
    mecn_set2 = reservoir.rows()[0][1::2][:columns]
    sample_wells = dwp.rows()[0][:columns]
    pcr_wells_set1 = pcr_plate.rows()[0][0::2][:columns]

    def mix_wells(pip, reps, vol, wells):
        for well in wells:
            pip.pick_up_tip()
            pip.mix(reps, vol, well)
            pip.drop_tip()

    def mecn_wash(vol, source):
        if mag_mod.status == 'engaged':
            mag_mod.disengage()
        m300.flow_rate.aspirate = asp_speed
        m300.transfer(vol, source, sample_wells)
        m300.flow_rate.aspirate = 94

    def remove_supernat(vol, source=sample_wells, dest=trash):
        m300.flow_rate.aspirate = asp_speed
        m300.transfer(vol, source, dest)
        m300.flow_rate.aspirate = 94

    def magnet(delay_mins):
        mag_mod.engage(height_from_base=mag_engage_height)
        ctx.delay(minutes=delay_mins, msg='Allowing beads to settle.')

    # Transfer Beads to Samples
    m20.transfer(bead_vol, sp2_beads, sample_wells, new_tip='always')

    # Mix Beads/Samples
    mix_wells(m300, 3, 50, sample_wells)

    # Transfer MeCN to Sample
    mecn_wash(mecn_wash1_vol, mecn_set1)

    # Mix Samples
    mix_wells(m300, 3, 300, sample_wells)

    # Allow Mixture to Settle
    ctx.delay(minutes=2, msg="Allowing mixture to settle.")

    # Series of Wash and Remove Steps
    magnet(5)
    remove_supernat(supernat_1_vol)
    mecn_wash(mecn_wash2_vol, mecn_set2)
    magnet(5)
    remove_supernat(supernat_2_vol)
    mecn_wash(mecn_wash3_vol, mecn_set2)
    magnet(5)
    remove_supernat(supernat_3_vol)
    mag_mod.disengage()

    # Transfer Elution Buffer
    m20.transfer(elution_buff_vol, elution_buffer, sample_wells)
    mix_wells(m20, 25, 20, sample_wells)
    magnet(5)
    remove_supernat(peptide_supernat_vol, pcr_wells_set1)

    # Pause to Swap PCR plate and Sample DWP positions
    ctx.pause('Move NEST 96-Well PCR Plate to Magnetic Module')

    # Remove plates from memory and reload them into new locations
    # User will swap Deep Well Plate with PCR plate on the magnetic module
    del ctx.deck['4']
    del ctx.deck['2']
    mag_mod = ctx.load_module("magnetic module gen2", 4)
    pcr_plate = mag_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    dwp = ctx.load_labware("stellarscientific_96_cluster_tubes_1200ul", 2)
    sample_wells_reloaded = dwp.rows()[0][:columns]
    pcr_wells_set2 = pcr_plate.rows()[0][1::2][:columns]

    # Engage, Transfer Peptide Supernatant, Add Formic Acid and iRT
    magnet(5)
    remove_supernat(peptide_supernat_vol, sample_wells_reloaded,
                    pcr_wells_set2)
    m20.transfer(formic_acid_vol, formic_acid, pcr_wells_set2)
    m20.transfer(irt_vol, irt, pcr_wells_set2)
