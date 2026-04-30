# Reverse Transcriptase Preparation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR Prep
	* Reverse Transcriptase

## Description
This is a plate filling protocol for a reverse transcriptase procedure. Up to 95 samples can be prepped using 4-in-1 tube racks filled with barcode primer mixes and a prepared enzyme mix in the final tube.

Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples this run (1-95)
* `Reagent Volume to Add`: Specify the volume of RT mix to add. Default is 4.7 uL
* `Well Plate Type`: Change between the BioRad plate in the OT-2 default labware library and the custom definition for Greiner 96 well plates with a circular well
* `P20 Mount`: Specify which side the single-channel P20 is mounted to

---

### Labware
* [Opentrons 20uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [BioRad 96 Well Plate](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Greiner Microplate, 96 Well, PP, V-Bottom](https://shop.gbo.com/en/usa/products/bioscience/microplates/96-well-microplates/96-well-polypropylene-microplates/651201.html)

### Pipettes
* [P20 Single Channel Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck-Setup

* Tube racks in slots 1, 2, 4, and 5 map directly to the 96 well plate. I.e. if 95 samples are specified all four tube racks will load in, RT mix will be in the bottom right well, C4, for slot 2. Well G12 will have primers added from slot 2, tube C3. If 13 samples are specified, the tube racks in slot 4 and 1 will load in, RT mix will be in well B2 in slot 1 (the 14th tube). Slot 1 A1's primer will add to well E1 in slot 3's well plate. Click [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/e54ada_rt/Tube+to+Plate+Mapping+for+RT.xlsx) for an explanatory spreadsheet

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/e54ada_rt/deck_layout.png)

### Reagent Setup

* Liquid Color Code:

![Color Code](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/e54ada_rt/color_code.png)

---

### Protocol Steps
1. RT mix is added from the final tube location to the sample plate, a single mix is done post-dispense to ensure full transfer of RT mix to the sample plate
2. 1 uL of primer is added from the tube rack to the plate, a single mix is done post-dispense to ensure full transfer of primer to the sample plate

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
e54ada
