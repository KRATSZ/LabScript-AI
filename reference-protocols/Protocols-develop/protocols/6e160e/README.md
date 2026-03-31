# Covid Sample Prep to 384 Plate

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps a 384 well plate on the temperature module with reaction mix and sample. Reaction mix is held in well one of a 12 well reservoir on the temperature module. Both temperature modules are held at 4C. The protocol uses a multi-channel to fill full plates, and a single channel to fill the last unfilled plate. Samples and reaction mix are filled by row, skipping columns.


Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples for this run.
* `P20 Mounts`: Specify which mount (left or right) for each the P20 Single-Channel and P20 Multi-Channel pipettes.


---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Corning 384 Well Plate 112 µL Flat](https://labware.opentrons.com/corning_384_wellplate_112ul_flat?category=wellPlate)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* [Bio-Rad 96 Well Plate 200 µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)


### Pipettes
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/pipettes/)
* [Opentrons P20 Multi-Channel Pipette](https://shop.opentrons.com/pipettes/)


---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6e160e/Screen+Shot+2022-03-14+at+10.29.50+AM.png)

Samples are layed out between plates in the following manner:
![plate layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/60feec/Screen+Shot+2022-03-15+at+9.52.19+AM.png)


---

### Protocol Steps
1. Set temp on mod to 4C.
2. Use 8ch & single channel pipette to transfer 6ul of reaction mix (multi dispense) to 384 plate following attached grid according to sample number, using the same tips.
[Need sample number to determine following steps]
3. [For 1-96 samples] Use 8ch & single channel pipette to transfer 4ul of eluted sample from Plate 1 to 384 plate following grid, dispose of tips after each aspiration.
4. [For 97-192 samples] Use 8ch & single channel pipette to transfer 4ul of eluted sample from Plate 2 to 384 plate following grid, dispose of tips after each aspiration.
5. [For 193-288 samples] Use 8ch & single channel pipette to transfer 4ul of eluted sample from Plate 3 to 384 plate following grid, dispose of tips after each aspiration.
6. [For 289-384 samples] Use 8ch & single channel pipette to transfer 4ul of eluted sample from Plate 4 to 384 plate following grid, dispose of tips after each aspiration.

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
6e160e
