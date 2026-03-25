# Custom CSV Mass Spec Sample Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Mass Spec

## Description
This protocol performs the preparation of samples from tubes to plates. It takes in a CSV file and uses the it to load the labware and make the necessary liquid transfers. It can support up to 2 sample plates.

Explanation of complex parameters below:
* `Input CSV File`: Upload a CSV file with the formatting shown in the block below for either One Plate or Two Plates:

**One Plate**
```
Sample ID,Slot number ,Rack position,Wellplate A position,Wellplate A well position
Sample1,1,1,3,A1
Sample2,1,2,3,A2
Sample3,1,3,3,A3
```

**Two Plates**
```
Sample ID,Slot number ,Rack position,Wellplate A position,Wellplate A well position,Wellplate B position,Wellplate B well position
Sample1,1,1,3,A1,6,A1
Sample2,1,2,3,A2,6,A2
Sample3,1,3,3,A3,6,A3
```

* `Sample Volume`: The amount of sample to transfer from the tubes to the plate.
* `Acetonitrile Transfer`: Whether to transfer acetonitrile into the plates (Steps 6-8).
* `P300 Single Channel GEN2 Mount Position`: Select the pipette mount position.
* `P300 Multi Channel GEN2 Mount Position`: Select the pipette mount position.
* `Sample Aspiration/dispense Flow rate`: Specify the flow rate of the sample liquid handling in uL/s.
* `MeCN Aspiration Flow Rate (uL/s)`: Specify aspiration/dispense flow rate for the multi-channel pipette.
* `Use Temperature Module`: Specify whether to use the temperature module on slots 3 and 6 with mounted deepwell plates. Note: if using the temperature modules, they should be placed in slots 3, and 6 respectively, in that order depending on running 1 or 2 plates.
* `Dispense Height in Destination Wells`: In millimeters.
* `PL Blowout Height`: In millimeters.
* `Airgap`: In microliters.
* `Reservoir Location`: Specify which reservoir column the MeCN will transfer to and from.
* `MeCN Dilution Location`: Specify slot MeCN is held in.
* `Multi-Channel Starting tip pick-up column (1-12)`: Specify which column on slot 10 tip rack to start picking up tips with the multi-channel pipette. 


---

### Labware
* TBD

### Pipettes
* [P300 Single Channel GEN2](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)
* [P300 Multi Channel GEN2](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)

---

### Deck Setup

**One Plate Example:**

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/459cc2/459cc2-layout.png)

### Reagent Setup
* Slot 7 Reservoir: Acetonitrile

---

### Protocol Steps
1. Aspirate 50 uL of the sample from tube rack using the single channel pippete P300. Add a 20 uL air gap.					
2. Dispense sample into a A1 of Plate 1. Use blowout after dispensing. (Repeat for same well on Plate 2 if needed).
3. Discard tip into the trash bin.
4. Repeat steps 1-3 for all wells in the CSV file.
5. Pick up tips with the multichannel pipette, transfer 100 uL of Acetonitrile to all wells in the plate.
6. Discard tip into the trashbin.

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
459cc2
