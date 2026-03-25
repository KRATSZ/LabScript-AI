# Distribution of PCR mastermix to MicroAmp 384 optical well plate or other plate

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol distributes PCR mastermix from a source NEST 12 well reservoir to a target Applied Biosystems Microamp optical 384 well 30 µL plate (or other PCR plate) with an 20 µL 8-channel pipette loaded in the left mount. The user can choose how many wells to transfer to (rounding up to the nearest number of columns) as well as how much volume to add to each well. The user can also choose whether they want to reuse tips, or pick up new tips for each transfer.

Explanation of parameters below:
* `Number of wells to distribute mastermix to`: How many wells to transfer mastermix to on the target plate. This will be rounded up to the nearest number of full columns.
* `Volume of mastermix`: Volume of mastermix to add to each well (µL)
* `Reuse tips?`: Yes: Reuse tips when distributing the mastermix. No: Drop the tips after each distribution, and pick up new tips before each aspiration.
* `Destination plate`: What type of plate to distribute mastermix to

---

### Labware
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [MicroAmp Optical 384-Well Reaction Plate with barcode](https://www.thermofisher.com/order/catalog/product/4309849)
* [20 µL filter tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

### Pipettes
* [20 µL multi-channel pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* PCR master-mix in the first well of the source reservoir on slot 1.

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/772041/deck2.jpg)

### Reagent Setup
* Source plate: slot 1
![Reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/772041/resv.jpg)

---

### Protocol Steps
1. Pick up tips (or re-use tips if a set of tips is already picked up, and the `reuse tips` setting is on) with the 20 µL multi-channel pipette
2. Aspirate the chosen volume of mastermix from the source reservoir
3. Distribute mastermix to the target plate
4. Drop the tips (optional)
4. Repeat steps 1 to 4 until the mastermix has been distributed to all wells  

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
772041
