# Luminex Assay Creating Replicates

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol replicates 6 or 7 isopaks from 1 or 2 source isopaks depending on the sample volume specified by the user according to the [Luminex MagPlex® Microspheres kit](https://www.luminexcorp.com/magplex-microspheres/#overview). Tips are removed from rows B, D, F, H of the tiprack to allow for the multi-channel pipette to access the isopaks.


Explanation of complex parameters below:
* `Number of Samples`: Specify whether running 24 or 48 samples. If running 24 samples, one isopak will be replicated into 7 isopaks. If running 48 samples, isopak 1 on slot 10 will supply empty isopaks in slots 1, 2, and 3, and isopak 2 on slot 11 will supply empty isopaks in slot 4, 5, and 6. See below for diagrams.
* `Use middle two columns?`: Specify whether using the middle two columns in source isopak(s). If this option is selected, the middle two columns of the source isopaks will be ignored, and the middle two tubes in the destination isopaks will also be ignored for dispensing.
* `Sample Volume`: Specify the sample volume to be replicated in microliters.
* `P300 Mount`: Specify which mount (left or right) to host the P300 Multi-Channel Pipette.

---

### Labware
* [Eppendorf Isopaks](https://www.eppendorf.com/dk-en/eShop-Products/Temperature-Control-and-Mixing/Accessories/IsoTherm-System-p-3880001166)
* [Greiner 96 well Chimney Bottom](https://shop.gbo.com/en/row/products/bioscience/microplates/non-binding-microplates/96-well-non-binding-microplates/655906.html)
* [Opentrons 300ul Tips](https://shop.opentrons.com/universal-filter-tips/)

### Pipettes
* [Opentrons P300 Multi-Channel Pipette](https://opentrons.com/pipettes/)


---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0e7175/Screen+Shot+2022-10-03+at+12.02.14+PM.png)
![deck layout2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0e7175/Screen+Shot+2022-10-03+at+12.02.30+PM.png)
---

### Protocol Steps
1. Pipette will aspirate as many multiples of the sample volume specified as possible.
2. Pipette will dispense sample volume from column to column of source to as many destination isopaks as possible, re-aspirating if needed.
3. Pipette changes tips between columns of source isopak.

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
0e7175
