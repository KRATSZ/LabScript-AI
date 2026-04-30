# Material Synthesis Prep with CSV Input


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol preps up to (4) 24 tube custom tube racks with unique volumes of reagents 1-18 coming from a 15mL tube rack, as well as a 50mL tube rack. CSV's for destination custom racks should all include the following header `Rack, Well, Label, DEAEMA (mL), AEMAm (mL), DIPAEMA (mL), DMAEMA (mL), MPC (mL), PEGMA500 (mL), HEMA (mL), PEGMA300 (mL), PEGMA950 (mL), GlyMA (mL), PHPMA (mL), Initiator (mL), CTA (mL), Initiator 2 (mL), CTA 2 (mL), Solv (mL), Solv2, Solv3`. Headers may include whatever nomenclature is desired, but must have the same number of columns. The initial volumes CSV informs the initial volume of all 15 tubes in slots 2 and 5, and includes the following as the header `Slot (2 or 5), Tube Position (A1, A2, etc.), Initial Volume (mL)`. Note: the initial volume CSV should include 18 rows not including the header - 15 for the 15 tube rack, and 3 for the 50mL rack. 


### Labware
* TWD_Tradewinds 24 Tube Rack with 4mL_Scintillation_Vials 4 mL
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 15 Tube Rack with Falcon 15 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 10 Tube Rack with Falcon 4x50 mL, 6x15 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/075bee/Screen+Shot+2022-11-09+at+1.54.16+PM.png)


### Protocol Steps
1. Pick up tip
2. Aspirate from A1 of tube rack at deck slot 2 at a height that doesnt penetrate the liquid past 75% of the tip length
3. Raise pipette to the top of the source tube at a rate of 10mm/s and delay 5s
4. Touch tip at a vertical offset of -1mm from the top of the tube
5. Move to A1 at deck slot 3 (custom tube rack)
6. Dispense at top of tube
7. Delay 5s and Blowout at a rate of 5uL/s
8. Repeat Steps 2-7 over destination A2-D6 using an array of volumes and flow rates, all using liquid from source location A1
9. Drop tip
10. Repeat steps 1-9 for each of the source tubes in the Falcon tube racks at deck slot 2 and deck slot 5
11. Mix each destination vial 200uL, 3 times
12. Repeat steps 1-11 for all destination vial racks at deck slots 7, 8, & 9


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app. by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions. if needed.
4. Upload your protocol file (.py extension. to the [OT App](https://opentrons.com/ot-app. in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
075bee
