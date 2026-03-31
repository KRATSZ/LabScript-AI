# flake8: noqa

metadata = {
    'protocolName': 'Bacterial Plating and Dilution',
    'author': 'Lachlan <lajamu@biosustain.dtu.dk',
    'apiLevel': '2.2'
}

def run(protocol):

	#Load Tips1
    tips20= [protocol.load_labware('opentrons_96_tiprack_20ul', '9')]


    p20Multi = protocol.load_instrument("p20_multi_gen2", "left", tip_racks=tips20)
  


    plate_type = "corning_96_wellplate_360ul_flat"
    locs = [4, 5, 6, 10, 11]

    dilutionPlates = [protocol.load_labware(plate_type, slot, label="Dilution Plates")
    				for slot in locs]

    agar_plate_type = "biorad_96_wellplate_200ul_pcr" #can be any 96 that isn't the same as dil plate
    agar_locs = [1, 2, 3, 7, 8]
    agar_plates = [protocol.load_labware(agar_plate_type, slot, label="Agar")
    				for slot in agar_locs]

        
    def spot(dest, spot_vol):
        """Takes a diluted transformed culture and spots the defined volume onto agar 
        in a Nunc omnitray"""

        SAFE_HEIGHT = 15  
        spotting_dispense_rate=0.025 
        p20Multi.move_to(dest.top(SAFE_HEIGHT))
        protocol.max_speeds["Z"] = 50
        p20Multi.move_to(dest.top(2))
        p20Multi.dispense(volume=spot_vol, rate=spotting_dispense_rate)
        p20Multi.move_to(dest.top(0))
        del protocol.max_speeds["Z"]
    
    def spot_then_dilute(sourceCol, agar_dest, destcol, spot_vol):
        p20Multi.aspirate(spot_vol, sourceCol)
        spot(agar_dest, spot_vol)
        p20Multi.transfer(10, sourceCol, destcol, mix_after=(5, 20), new_tip="never")
        
    
    def spot_dilute_plate(plate, agar, spot_vol):
        p20Multi.pick_up_tip()
        for col in range(1, 10):
            w = "A"+str(col)
            x = "A" + str(col+1)
            spot_then_dilute(plate[w], agar[w], 
                             plate[x], spot_vol)
            #Spot final dilution THIS S THE PROBLEM, DOUBLE UP WITH LINE 52-55
            p20Multi.aspirate(spot_vol, plate[x])
            spot(agar[x], spot_vol)
        p20Multi.drop_tip()
        
    for pl, ag in zip(dilutionPlates, agar_plates):
        spot_dilute_plate(pl, ag, 5)
        
    protocol.comment("Run Complete!")
        
        


    

