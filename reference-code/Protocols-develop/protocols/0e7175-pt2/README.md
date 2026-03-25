# Luminex Assay Bead and Antibody Transfer

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol provides sample and reagents to 2 96 well plates according to the [Luminex MagPlex® Microspheres kit](https://www.luminexcorp.com/magplex-microspheres/#overview). Column 1 of the source isopak 1 is dispensed into rows A, C, E, G of the destination plate 1 in columns 1 and 2. Column 2 of the source isopak is dispensed into rows A, C, E, G of the destination plate 1 in columns 3 and 4, etc. Column 1 of the source isopak 2 is dispensed into rows B, D, F, H of the destination plate 1 in columns 1 and 2, etc. This is then repeated for destination plate 2. Tips are removed from rows B, D, F, H of the tipracks on slot 10 and 11 to allow for the multi-channel pipette to access the isopaks. The tiprack on slot 9 should be a full tip rack.


Explanation of complex parameters below:
* `Sample Volume`: Specify the sample volume to be replicated in microliters.
* `Use middle two columns?`: Specify whether using the middle two columns in source isopaks. See below for deck map if selected. If selected, the protocol will pause after the first 96 plate is filled to prompt the user to replace the alternate tip rack on slot 11.
* `Antibody Volume`: Specify the sample volume to be replicated in microliters.
* `SA-PE Volume`: Specify the SA-PE volume to be replicated in microliters.
* `P300 Mount`: Specify which mount (left or right) to host the P300 Multi-Channel Pipette.

---

### Labware
* [NEST 12 Well Reservoir 195mL](https://shop.opentrons.com/consumables/)
* [Eppendorf Isopaks](https://www.eppendorf.com/dk-en/eShop-Products/Temperature-Control-and-Mixing/Accessories/IsoTherm-System-p-3880001166)
* [Greiner 96 well Chimney Bottom](https://shop.gbo.com/en/row/products/bioscience/microplates/non-binding-microplates/96-well-non-binding-microplates/655906.html)
* [Opentrons 300ul Tips](https://shop.opentrons.com/universal-filter-tips/)

### Pipettes
* [Opentrons P300 Multi-Channel Pipette](https://opentrons.com/pipettes/)


---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0e7175/Screen+Shot+2022-10-03+at+12.27.35+PM.png)
![deck layout3](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0e7175/Screen+Shot+2022-10-11+at+11.15.38+AM.png)
![deck layout2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0e7175/Screen+Shot+2022-10-03+at+12.32.42+PM.png)
---

### Protocol Steps
1. 50ul of beads added to all wells in 96 well plates.
2. Pause step for incubation. User selects "resume" in the Opentrons app.
3. Sample added from source isopaks according to the scheme provided in description.
4. Pause step for incubation. User selects "resume" in the Opentrons app.
5. Antibody volume added to all wells in 96 well plates.
6. Pause step for incubation. User selects "resume" in the Opentrons app.
7. 75ul SA-PE added to all wells in 96 well plates.

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
0e7175-pt2
