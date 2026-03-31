# Bead-Based Nucleic Acid Clean-Up

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* DNA/RNA Extraction

## Description
This is a bead-based purification of nucleic acids using either BioRad 96 well plates or Grenier 96 well plates. Using P300 single and multi channel pipettes we have flexibility using 4-in-1 tube racks or 12 well reservoirs to hold beads. The beads can be diluted with 40% PEG 8000 mixtures or left neat from the reagent bottle.

Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples this run (1-96)
* `Reaction Volume`: Specify the starting sample volume in uL for the first plate
* `Bead Ratio`: Specify the ratio of beads to sample volume with a float. Default is 1.8
* `Elution Volume`: Specify the volume of elution liquid to use and subsequently transfer to the final plate in uL
* `P300 Multi Channel Pipette Mount`: Specify which side the multi-channel P300 is mounted to. The single-channel P300 will default to the opposite side
* `Well Plate Type`: Change between the BioRad plate in the OT-2 default labware library and the custom definition for Greiner 96 well plates with a circular well
* `Flash`: Specify whether the robot will flash on pauses for tip rack refills and trash alerts

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [NEST 12 Reservoir 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 200uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [BioRad 96 Well Plate](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Greiner Microplate, 96 Well, PP, V-Bottom](https://shop.gbo.com/en/usa/products/bioscience/microplates/96-well-microplates/96-well-polypropylene-microplates/651201.html)

### Pipettes
* [P300 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [P300 Single Channel Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup

* Tube rack in slot 6 is only used when under 7 samples are specified. Beads are loaded in A1 of tube rack for 1-6 samples. If samples are 7-96 beads are loaded in slot 3, well 12

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/e54ada/deck_layout.png)

### Reagent Setup

* Liquid Color Code:

![Color Code](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/e54ada/liquids.png)

* Reservoir 1: Slot 3

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/e54ada/resv.png)

* NOTE ON REAGENT LOADING:
  Ethanol should be loaded into slots 1-4 in deck slot 3. Ethanol will be aspirated equally from all 4 wells. The minimum volume for the NEST reservoir is 1.5 mL. E.g. if 4 mL of ethanol is needed in total it should be split between the four wells with an extra 500 uL added to reach 1.5 mL per well.

  Additionally, the ethanol wash volume varies depending on the well plate being used. 200 uL per wash per sample will be used for the Greiner plate while 120 uL per wash per sample will be used for the BioRad plate.

* NOTE ON SAMPLE NUMBERS:
  This protocol is very flexible in sample numbers but with one caveat. Multiples of 8 to run full columns is recommended for efficiency. Running 15 samples will take much longer than 16 samples as 7 samples in the second column will utilize the single-channel pipette. This is a trade off of total run time for reagent efficiency. If you want to run 15 samples and are willing to use extra reagent, enter 16 samples and leave the 16th well empty in column 2.

* NOTE ON SLOT 2's EMPTY TIP BOX
  This protocol uses an empty 300uL tip box in slot 2 for tip parking and reuse across steps. This allows easy tip re-use for supernatant removal and wash steps. Proper tip rack calibration is still necessary for good results

---

### Protocol Steps
1. Beads are added to the sample plate according to the supplied bead ratio parameter. The sample/bead mixture is mixed. The beads are re-mixed every 3 samples to ensure homogeneity in the reagent well.
2. The beads are incubated for 10 minutes in the samples before the magnetic module is engaged for 7 minutes
3. The supernatant is removed and deposited in the waste container in slot 11
4. Ethanol is added to the wells to wash beads. 200 uL is added for the Greiner plates and 120 uL for BioRad plates
5. A 2 minute delay occurs to allow beads to re-pellet after ethanol wash
6. Ethanol is removed from samples and deposited in the waste container in slot 11
7. Steps 4-6 are repeated for a second ethanol wash
8. Water is added to the samples to elute according to the set parameters below and mixed
9. A 5 minute delay occurs to allow elution to occur followed by the magnetic module being engaged for 7 minutes
10. The elution solution, now separated from the beads, is aspirated and dispensed in the awaiting plate in slot 10

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
