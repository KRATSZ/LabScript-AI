# Life Magnetics C-Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Nucleic Acid Purification

## Description
This protocol extracts RNA with a temperature module and magnetic module. User has the choice to include a "Waste water mode" which consists of adding and mixing binding buffer on magnetically engaged beads. Tips are tracked between protocols with the protocol pausing and prompting the user to replace tip racks when a tip rack is depleted.

Explanation of complex parameters below:
* Most customizable variables below are in reference to the original protocol request coded by the user. All additional parameters are explained:
* `Reset Tipracks`: Select `yes` to pick up the tip from A1 on both the 200ul and 300ul tip racks. Select `no` to pick up the tips for both tip racks from where the previous run left off.
* `Remove supernatant aspiration height (mm)`: Select aspiration height from the bottom of the well to remove supernatant.
* `Length from side of the well opposite magnetically engaged beads (mm)`: Specify the distance to aspirate from the side of the well opposite the magnetically engaged beads. A values of 1 is the side of the well, a values of 4.1 is the middle of the well.
* `P300 Single GEN2 Mount`: Select which side (left or right) to mount P300 single channel pipette.


---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/collections/lab-plates/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Opentrons 200uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)


### Pipettes
* [P300 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/19313a/Screen+Shot+2021-07-22+at+3.55.36+PM.png)

### Reagent Setup
* Tube rack on slot 4
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/19313a/Screen+Shot+2021-07-22+at+3.56.17+PM.png)

---

### Protocol Steps
1. Temperature reached, magnetic module engaged
2. If normal mode, user does first mix step as temperature is reached, binding buffer added and mixed, 200ul of supernatant removed.
3. If wastewater mode, remove up to 1.5 ml of storage buffer in samples
4. RPS wash, remove supernatant in samples
5. Two ethanol washes, remove supernatant in samples
6. Settling time, drying, remove 300ul from sample wells.
7. Aspirate elution volume, mix
8. Dispense in temperature module (well to well transfer).
9. Mix, incubate (3 times)
10. Dispense in magnetic module (well to well transfer), engage magnet
11. Move final volume to next column or each triplicate on mag deck (well to well transfer)

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
19313a
