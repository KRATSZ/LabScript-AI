# Custom PCR Setup from CSV

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
Theis protocol is used to set up DNA samples for analysis with [Life Technologies QuantStudio™ 12K Flex Real-Time PCR System, OpenArray™ block, Accufill™ System](https://www.thermofisher.com/order/catalog/product/4471090?SID=srch-srp-4471090#/4471090?SID=srch-srp-4471090). Using the [P20 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette), two PCR preps are accomplished. During the first prep, samples are reformatted and transferred from a 96-well plate to another 96-well plate before amplification. Once amplification is complete, the user returns the amplified plate and the second prep occurs - this time samples are transferred from the 96-well plate to a 384-well plate.


Explanation of complex parameters below:
* **Transfer CSV**: CSV file that contains the transfer information. It should contain the following header: SourcePos,SampleID,PreampPos,LoadPos1,LoadPos2
* **P20 Single Mount**: Select which mount the [P20 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) is attached to.

*Note*: In the current configuration, up to 95 samples can be completed in one run.

---


### Labware
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [NEST 96-Well Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Corning 384-Well Plate](https://labware.opentrons.com/corning_384_wellplate_112ul_flat?category=wellPlate)
* [Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* 1.5mL [Microcentrigue Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)

### Pipettes
* [P20 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

### Reagents
* Preamp Mastermix
* OpenArray Mastermix


---

### Deck Setup
</br>
**Slot 1**: Source Plate ([NEST 96-Well Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt))
</br>
</br>
**Slot 2**: Preamp Plate ([NEST 96-Well Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt))
</br>
</br>
**Slot 3**: Loading Plate ([Corning 384-Well Plate](https://labware.opentrons.com/corning_384_wellplate_112ul_flat?category=wellPlate))
</br>
</br>
**Slot 4**: [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips) (Tiprack 1)
</br>
</br>
**Slot 5**: [Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 24-Tube Topper
</br>
</br>
**Slot 7**: [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips) (Tiprack 2)
</br>
</br>
**Slot 10**: [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips) (Tiprack 3)
</br>
</br>

### Reagent Setup
[Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 24-Tube Topper + 1.5mL [Microcentrigue Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* Well A1: Preamp Mastermix
* Well D6: OpenArray Mastermix

---

### Protocol Steps
1. The user will be prompted to load the Source Plate and Preamp Plate (if not already loaded) and make sure that enough Preamp Mastermix is in the tube in A1 of the Tube Rack.
2. The P20 will pick up a tip, then distribute 2.5µL of Preamp Mastermix to all wells listed in the **PreampPos** column of the Transfer CSV. The P20 will mix the Mastermix two times, aspirate 20µL, then dispense 2.5µL in each well, repeating this process until complete. When done, the pipette will return any extra Mastermix to the tube, then drop the tip.
3. For each location in **SourcePos** and **PreampPos**, the P20 will pick up a tip, go to the SourcePos and mix three times, transfer 2.5µL to the PreampPos, mix three times, then drop the tip.
4. Once all transfers are completed for the above step, the user will be prompted to remove the plate for amplification. When ready to begin part two, the user will be prompted to load the Preamp Plate and Loading Plate (if not already loaded) and make sure that enough OpenArray Mastermix is in the tube in D6 of the Tube Rack.
5. The P20 will pick up a tip, then distribute 3.75µL of OpenArray Mastermix to all wells listed in the **LoadPos1** and **LoadPos2** columns of the Transfer CSV. The P20 will mix the Mastermix two times, aspirate 15µL, then dispense 3.75µL in each well, repeating this process until complete. When done, the pipette will return any extra Mastermix to the tube, then drop the tip.
6. For each line of the Transfer CSV, the P20 will pick up a tip, go to the **PreampPos** and mix three times, transfer 1.75µL to the **LoadPos1**, mix three times, then drop the tip. This process will be repeated with the **LoadPos2**
7. Once complete, the user will be alerted that they can move on to the next step of the process (off deck).


### Process
1. Input your protocol parameters above.
2. Download your protocol.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions), if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3d942d
