# flake8: noqa

metadata = {
    'author': 'Michael Fichtner <michael.fichtner@mdc-berlin.de>',
    'description': 'The protocol is intended to prepare and run a PCR \
                    using the opentrons cycler module',
    'apiLevel': '2.11'
            }

# For 50 ml falcons
conical_volume = 3.27   # in ml
height_increase = 1.63   # mm per ml


def sorting_tips(pip):
    '''This function will sort the tips in a tip box back to front. Useful if
       if only a few tips have been used.
       Takes roughly 20 min per box'''
       
    for rack in pip.tip_racks:
        if rack.next_tip() and not rack.next_tip().well_name == "A1":
            well_number = 0
            while rack.next_tip():
                pip.pick_up_tip()
                pip.drop_tip(rack.wells()[well_number])
                well_number += 1

def take_from_falcon(vol, tube, solution_vol, pip, rate=1):
    '''Helper function to track changes of the volume in falcon tubes and
    adjusts the height of the pipette accordingly.
    Returns the remaining volume of a given liquid.'''
    
    if solution_vol > conical_volume:
        aspirate_well = tube.bottom(z=((solution_vol/1000)*height_increase)-(vol/1000))
    else:
        aspirate_well = tube.bottom(z=2)
    solution_vol -= vol
    pip.aspirate(vol, aspirate_well, rate=rate)
            
    return solution_vol

def dispense_to_falcon(vol, tube, solution_vol, pip, rate=1, mix=False):
    '''Helper function to track changes of the volume in falcon tubes and
    adjusts the height of the pipette accordingly.
    Returns the remaining volume of a given liquid.'''
    
    if solution_vol > conical_volume:
        z_height = ((solution_vol / 1000) * height_increase) - (vol/1000)
    else:
        z_height = 2
    
    dispense_well = tube.bottom(z=z_height)
    solution_vol += vol
    pip.dispense(vol, dispense_well, rate=rate)
    if mix:
        pip.mix(15, 200, dispense_well.bottom(z=z_height), rate=rate)
    return solution_vol

def transfer_to_tube(total_vol, source, source_vol, target, target_vol,
                     pip, new_tip=True, rate=1):
    pip.pick_up_tip()
    while total_vol >= 220:
        source_vol = take_from_falcon(200, source, source_vol, pip, rate)
        target_vol = dispense_to_falcon(200, target, target_vol, pip)
        total_vol -= 200
        if new_tip:
            pip.drop_tip()
            pip.pick_up_tip()
        
    if total_vol <= 200:
        source_vol = take_from_falcon(total_vol, source, source_vol, pip, rate)
        target_vol = dispense_to_falcon(total_vol, target, target_vol, pip)
        total_vol = 0
    elif total_vol > 200 and total_vol < 220:
        split_vol = total_vol / 2
        source_vol = take_from_falcon(split_vol, source, source_vol, pip, rate)
        target_vol = dispense_to_falcon(split_vol, target, target_vol, pip)
        if new_tip:
            pip.drop_tip()
            pip.pick_up_tip()
        source_vol = take_from_falcon(split_vol, source, source_vol, pip, rate)
        target_vol = dispense_to_falcon(split_vol, target, target_vol, pip)
        total_vol = 0
    else:
        raise ValueError("Wrong total volume. That should not happen! Please \
                         contact the protocol developer.")
    pip.blow_out()
    pip.drop_tip()
    
    return source_vol, target_vol

def distribute_multiple(vol, source, targets: list, pip,
                        new_tip=True, source_vol=200):
    ''' The distribute() function has a bug that would cause contamination
        of the source vial because it ignores the new_tip=always.
        Thus I wrote my own. '''
        
    total_wells = len(targets)
    if pip.max_volume == 300:   # That means p300
        excess_vol = 0    
        max_wells_per_step = (200 - excess_vol) // vol
    elif pip.max_volume == 20:
        excess_vol = 0
        max_wells_per_step = (20 - excess_vol) // vol
    else:
        raise Exception("Cannot determine the type of pipette.")
    assert max_wells_per_step > 0, "Volume per well is too large" # TODO: make a fall back to transfer
    
    pip.pick_up_tip()
    while total_wells > max_wells_per_step:
        if (source_vol / 1000 ) > conical_volume:
            z_height = ((source_vol / 1000) * height_increase) - (vol / 1000)
        else:
            z_height = 1
        vol_needed = (max_wells_per_step * vol) + excess_vol
        pip.aspirate(vol_needed, source.bottom(z=z_height))
        for i in range(int(max_wells_per_step)):
            pip.dispense(vol, targets.pop(0))
        if new_tip:
            pip.drop_tip()
            pip.pick_up_tip()
        total_wells -= max_wells_per_step
        source_vol -= vol_needed
    if total_wells > 0 and total_wells <= max_wells_per_step:
        vol_needed = (total_wells * vol) + excess_vol
        if (source_vol / 1000 ) > conical_volume:
            z_height = ((source_vol / 1000) * height_increase) - (vol / 1000)
        else:
            z_height = 1
        pip.aspirate(vol_needed, source.bottom(z=z_height))
        for i in range(len(targets)):
            pip.dispense(vol, targets.pop(0))
        source_vol -= vol_needed
    pip.drop_tip()
    
    return source_vol
    
    
def run(prot):
    ############## Change variables here ##################
    reaction_vol = 100     # total volume of PCR reaction per well (in ul)
    sample_no = 9        # Number of different samples (excluding water) (1-12)
    sample_vol = 1         # ul per PCR reaction 
    replicates = 3         # number of replicates per sample (1-95)
    MM_no = 3              # Number of Mastermixes (1-3)
    repetitions = 35 
    cycler_profile = [{'temperature': 95, 'hold_time_seconds': 30},
                      {'temperature': 60, 'hold_time_seconds': 30},
                      {'temperature': 72, 'hold_time_seconds': 30}]
    
    ######## Hard coded values that you may want to change
    sort_tips = True   # Sort the tips back to front at the end
    fast = True        # If False: Performs homing steps in between, not needed anymore
    init_denat_temp = 98 # degrees celsius for initial denaturation
    init_denat_time = 120 # seconds for initial denaturation
    
    # Calculate amount needed per sample:
    vol_Buffer = reaction_vol / 10
    vol_Primers = reaction_vol / 20
    vol_dNTPs = reaction_vol / 50
    vol_Polymerase = reaction_vol / 100
    vol_MgCl2 = reaction_vol / 50
        
    excess = 1.1          # Percentage of excess for MM
    
    ######## Do not change anything below here ############
    ######## unless you know what you are doing ###########
    #-----------------------------------------------------#

    water_needed = reaction_vol - vol_Buffer - (vol_Primers * 2) - vol_dNTPs - \
                   vol_Polymerase - sample_vol - vol_MgCl2
    wells_needed = (sample_no * replicates) + 1  # per mastermix, the +1 is for water control
    assert wells_needed * MM_no <= 96, "Not enough free wells for MM"
    assert water_needed >= 0, "Reaction volume is too large"
    assert sample_no <= 12, "Only 12 different samples are allowed at the moment."
    
    
    tiprack_1_p300 = prot.load_labware('opentrons_96_filtertiprack_200ul', 2)
    #tiprack_2_p300 = prot.load_labware('opentrons_96_filtertiprack_200ul', 5)
    tiprack_1_p20 = prot.load_labware('opentrons_96_filtertiprack_20ul', 1)
    
    
    tube_rack = prot.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 6)
    huge_tubes_rack = prot.load_labware(
        'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 9)
        
    p300 = prot.load_instrument('p300_single_gen2', 'left',
                                tip_racks=[tiprack_1_p300]) #, tiprack_2_p300])
    p20 = prot.load_instrument('p20_single_gen2', 'right',
                               tip_racks=[tiprack_1_p20])
    
    tempdeck = prot.load_module('temperature module gen2', '3')
    cool_rack = tempdeck.load_labware('opentrons_24_aluminumblock_nest_1.5ml_screwcap')
    
    
    cycler = prot.load_module('Thermocycler Module') # By default: Cylcer covers slots 7,8,10,11
    pcr_plate = cycler.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul')
    
    water = huge_tubes_rack.wells_by_name()['A3']    
    complete_MMs = [huge_tubes_rack.wells_by_name()['A4'],
                    huge_tubes_rack.wells_by_name()['B3'],
                    huge_tubes_rack.wells_by_name()['B4']
                    ]
   
    dNTPs = cool_rack.wells_by_name()['A1']
    polymerase = cool_rack.wells_by_name()['A6']
    buffer = tube_rack.wells_by_name()['D1']        
    mgcl2 = tube_rack.wells_by_name()['D2']
    primers_fw = [tube_rack.wells_by_name()['A1'],
                  tube_rack.wells_by_name()['A2'],
                  tube_rack.wells_by_name()['A3']
                  ]

    primers_rev = [tube_rack.wells_by_name()['B1'],
                  tube_rack.wells_by_name()['B2'],
                  tube_rack.wells_by_name()['B3']
                  ]
    
    assert MM_no <= len(complete_MMs), "More MMs required than tubes available"    
    
    sample_tubes = tube_rack.wells()[12:12+sample_no]
        
    total_water_needed = water_needed * wells_needed * MM_no * excess + sample_vol
    total_buffer_needed = vol_Buffer * wells_needed * excess * MM_no
    
    ######### Protocol starts here ################
    prot.comment("Water needed: " + str(total_water_needed))
    prot.comment("Buffer_needed: " + str(total_buffer_needed))
    prot.comment("Primer_needed (each): " + str(vol_Primers * wells_needed * excess))
    prot.comment("dNTPs needed: " + str(vol_dNTPs * wells_needed * excess))
    prot.comment("MgCl2 needed: " + str(vol_MgCl2 * wells_needed * excess))
    prot.comment("Polymerase needed: " + str(vol_Polymerase * wells_needed * excess))

    # will not wait until 4 degrees are reached
    tempdeck.start_set_temperature(4)
    cycler.set_block_temperature(4)
    
    # Preparing Mastermixes
    for i in range(MM_no):
        mastermix_volume = 0
        # Transfer water -> I assume that we will never use less than 20 ul water
        water_to_transfer = water_needed * wells_needed * excess
        total_water_needed, mastermix_volume = transfer_to_tube(water_to_transfer,
                                                                water, total_water_needed,
                                                                complete_MMs[i], mastermix_volume,
                                                                new_tip=False, pip=p300)
        
        # Transfer Buffer
        buffer_to_transfer = vol_Buffer * wells_needed * excess
        if buffer_to_transfer > 20:
            pipette = p300
        else:
            pipette = p20
        total_buffer_needed, mastermix_volume = transfer_to_tube(buffer_to_transfer,
                                                                buffer, total_buffer_needed,
                                                                complete_MMs[i], mastermix_volume,
                                                                new_tip=True, pip=pipette)
        
        # Transfer Primers
        primers_to_transfer = vol_Primers * wells_needed * excess
        if primers_to_transfer > 20:
            pipette = p300
        else:
            pipette = p20
        _ , mastermix_volume = transfer_to_tube(primers_to_transfer,
                                                primers_fw[i], primers_to_transfer,
                                                complete_MMs[i], mastermix_volume,
                                                new_tip=True, pip=pipette)
        _ , mastermix_volume = transfer_to_tube(primers_to_transfer,
                                                primers_rev[i], primers_to_transfer,
                                                complete_MMs[i], mastermix_volume,
                                                new_tip=True, pip=pipette)
        
        # Transfer dNTPs
        dNTPs_to_transfer = vol_dNTPs * wells_needed * excess
        if dNTPs_to_transfer > 20:
            pipette = p300
        else:
            pipette = p20     
        _ , mastermix_volume = transfer_to_tube(dNTPs_to_transfer,
                                                dNTPs, dNTPs_to_transfer,
                                                complete_MMs[i], mastermix_volume,
                                                new_tip=True, pip=pipette)
        
        # Transfer MgCl2
        if vol_MgCl2 > 0:
            mgcl2_to_transfer = vol_MgCl2 * wells_needed * excess
            if mgcl2_to_transfer > 20:
                pipette = p300
            else:
                pipette = p20   
            _ , mastermix_volume = transfer_to_tube(mgcl2_to_transfer,
                                                    mgcl2, mgcl2_to_transfer,
                                                    complete_MMs[i], mastermix_volume,
                                                    new_tip=True, pip=pipette)
        # Transfer Polymerase
        polymerase_to_transfer = vol_Polymerase * wells_needed * excess
        if polymerase_to_transfer > 20:
            pipette = p300
        else:
            pipette = p20
        _ , mastermix_volume = transfer_to_tube(polymerase_to_transfer,
                                                polymerase, polymerase_to_transfer,
                                                complete_MMs[i], mastermix_volume,
                                                new_tip=True, pip=pipette)
        
        # Mixing
        p300.pick_up_tip()
        mixes = 10
        for height in range(1,
                            int((mastermix_volume / 1000) * height_increase) + 5,
                            1):
            p300.mix(mixes, 200, complete_MMs[i].bottom(z=height), rate=3)
        p300.drop_tip()
        
    cycler.open_lid()
    # I had the feeling the robot drifts a bit, hence the homing step.
    if not fast:
        prot.home()

    # TODO: Check if below can be adjusted to make it easier to read
    
    # Transferring MM to plate   
    
    #Note: If more than 1 Master Mix is used the skip_wells variable helps to
    #      make the final layout easier. If the samples + water are not
    #      multipes of 8, the last wells will be left free so that the first
    #      sample will always be in row A.
      
    skip_wells = 8 - (wells_needed % 8) # Needed to make an easier layout if multiple Mastermixes are used.
    if skip_wells == 8: skip_wells = 0
    for i in range(MM_no):
        if reaction_vol > 20:
            pipette = p300
        else:
            pipette = p20

        mastermix_volume = distribute_multiple(reaction_vol-sample_vol, complete_MMs[i],
                                               pcr_plate.wells()[i*wells_needed+(i*skip_wells):(1+i)*wells_needed+(i*skip_wells)],
                                               pip=p300, new_tip=False,
                                               source_vol=mastermix_volume)
    
    
    # Transferring samples to plate
    prot.comment("######### Transferring samples into Plate ###########")
    for MM in range(MM_no):
        next_MM = (skip_wells + wells_needed) * MM
        for j in range(sample_no):
            distribute_multiple(sample_vol, sample_tubes[j],
                                pcr_plate.wells()[next_MM+(j*replicates):next_MM+(j*replicates+replicates)],
                                p20)

        p20.distribute(
            sample_vol, water, pcr_plate.wells()[next_MM+wells_needed - 1], 
            new_tip='always')
    
    # Mix each well
    for MM in range(MM_no):
        next_MM = (skip_wells + wells_needed) * MM
        for j in range(sample_no):
            p300.pick_up_tip()
            for well in pcr_plate.wells()[next_MM+(j*replicates):next_MM+(j*replicates+replicates)]:
                p300.mix(3, 60, well)
            p300.drop_tip()

    ############ Starting the cycler
    cycler.set_lid_temperature(105)
    cycler.close_lid()
    
    # Initial denaturation
    cycler.set_block_temperature(init_denat_temp,
                                 hold_time_seconds=init_denat_time,
                                 block_max_volume=reaction_vol)
    # Actual run
    rep_split = int(repetitions / 5)
    for i in range(rep_split):
        # Since there is no way to tell at which cycle the PCR currently is,
        # I print every 5 cycles a message to get an estimate how long is left.
        cycler.execute_profile(steps=cycler_profile, repetitions=5,
                           block_max_volume=reaction_vol)
        prot.comment("Cycles completed: " + str((i+1)*5))
    
    remaining_reps = repetitions % 5
    if remaining_reps > 0:
        cycler.execute_profile(steps=cycler_profile, repetitions=remaining_reps,
                           block_max_volume=reaction_vol)
        
    # Final extension
    cycler.set_block_temperature(72, hold_time_seconds=300,
                                 block_max_volume=reaction_vol)
    
    cycler.set_block_temperature(4, block_max_volume=reaction_vol)
    
    ### Calcuating last required tips.
    ### Specifically requested by our lab staff.
    last_p20_tip = "error"
    for rack in p20.tip_racks:
        if rack.next_tip() and not rack.next_tip().well_name == "A1":
            last_p20_tip = rack.next_tip()
    last_p300_tip = "error"
    for rack in p300.tip_racks:
        if rack.next_tip() and not rack.next_tip().well_name == "A1":
            last_p300_tip = rack.next_tip() 
            
    if sort_tips:
        sorting_tips(p20)
        sorting_tips(p300)
    
    prot.comment("######### Last required tips ###########")
    prot.comment("P20: " + str(last_p20_tip))
    prot.comment("P300: " + str(last_p300_tip))
    
    