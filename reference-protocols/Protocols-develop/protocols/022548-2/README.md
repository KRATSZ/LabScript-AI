# Sample transfer and bead mastermix addition

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* DNA Extraction

## Description
This protocol transfers samples from tubes in up to 3 PRL tuberacks to a destination plate followed by resuspending a bead/binding buffer mastermix before transfering it to the samples on the plate.

Links:
* [Part 1: Master Mix Assembly](./022548)
* [Part 2: Master Mix Distribution and Sample Transfer](./022548-2)


Explanation of parameters below:
* `Number of samples in tuberack 1 slot 10-11`: How many samples to transfer from rack 1: 1 to 32
* `Number of samples in tuberack 2 slot 7-8`: 0 to 32
* `Number of samples in tuberack 3 slot 4-5`: 0 to 32
* `Master mix wells location`: Informs the protocol which wells of the reservoir contain mastermix, starting from A1 on the very left. For example 1-4 to specify wells A1 to A4. This parameter may also be a single number instead of a range
* `Mastermix max volume per well (mL)`: Informs the protocol what the maximal volume of mastermix is in each reservoir well, default is 9.54 mL
* `Mastermix mixing rate multiplier`: Controls the flow rate of mixing, 1.0 means standard flow rate, less is slower and more is faster.
* `mastermix aspiration flow rate multiplier`: Controls the rate of aspiration of mastermix from the reservoir wells
* `mastermix dispension flow rate multiplier`: Controls the rate of dispension of mastermix into wells on the target plate
* `Mount for 300 uL single channel pipette`: Left or right
* `Mount for 300 uL multi channel pipette`: Left or right
* `Pause after mixing the mastermix for vortex/resuspension?`: Optional pause after (re-)mixing the mastermix where the reservoir may be taken out for manual resuspension such as vortexing, nutation or shaking if resuspension by pipetting is deemed insufficient.

---

### Labware
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* PRL tuberack for 32 15 mL tubes
* [Thermo Fisher Kingfisher 96 deepwell plate 2 mL](https://www.thermofisher.com/order/catalog/product/A43075)


### Pipettes
* [P300 multi-Channel (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P300 single-Channel (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [300 uL tipracks](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)
* [Opentrons 200 µL filter tiprack](https://shop.opentrons.com/opentrons-200ul-filter-tips/)

---

### Deck Setup
* Load 300 ul tip racks in order 6-3. Load tube racks in order from top down. Load samples in order down the column in each tube rack. Tube racks should be filled fully before proceeding to next tube rack. For example, 33 samples total would mean 32 in the top most tube rack and 1 sample in the middle tube rack.


![Deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/022548/Screen+Shot+2022-08-25+at+3.01.33+PM.png)

### Reagent Setup
* Mastermix Reservoir: Specify what wells contain mastermix starting from A1 in the parameter section - See parameter section above.

---

### Protocol Steps
1. Transfer samples from the tubracks to the target plate in row order using the single channel 300 uL pipette using 200 uL filter tips.
2. Mix the bead/binding buffer mastermix 7 times.
3. Transfer mastermix to samples using the multi-channel 300 uL pipette with regular 300 uL tips.

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
022548-2
