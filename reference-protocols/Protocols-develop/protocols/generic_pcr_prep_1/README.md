# Generic PCR Prep Part 1 - Mastermix Creation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
    * Generic Mastermix Assembly

## Description
Part 1 of 2: Master Mix Assembly

This protocol allows your robot to create a master mix solution using any reagents stored in one to three different pieces of labware such as a tube racks, well plates, and 12 well reservoirs. The master mix will be created in well A1 of the trough of the chosen reservoir. The ingredient information will be provided as a CSV file. See Additional Notes for more details.

Links:
* [Part 1: Master Mix Assembly](./generic_pcr_prep_1)
* [Part 2: Master Mix Distribution and DNA Transfer](./generic_pcr_prep_2)


Explanation of parameters below:
* `right pipette type`: Pipette for the right mount
* `Left pipette type`: Pipette for the left mount
For the pipette choices it is important that the pipettes selected will cover the range of volumes used in the protocol
* `master mix .csv file`: Here, you should upload a .csv file formatted in the following way, being sure to include the header line:

![csv_layout](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/1473-acies-bio/CSV.png)
* `Left pipette: Filter or regular tips?` Select whether you want unfiltered or filtered tips. The protocol will load the appropriate tips, e.g. 20 uL tips for a 20 uL pipette, 1000 uL filtered/nonfiltered for a 1000 uL pipette etc.
* `Right pipette: Filter or regular tips?` Select whether you want unfiltered or filtered tips. The protocol will load the appropriate tips, e.g. 20 uL tips for a 20 uL pipette, 1000 uL filtered/nonfiltered for a 1000 uL pipette etc.
* `Reagent labware 1` Choose the appropriate labware (such as tube racks or well plates) for your reagents, you may choose aluminum blocks if you intend to use a temperature module. This is referred to as "slot 1" in the .csv
* `Reagent labware 2` (Optional) Choose a secondary unit of labware for your reagents, you may choose aluminum blocks if you intend to use a temperature module. This is referred to as "slot 2" in the .csv
* `Twelve well Reservoir and mastermix destination` Select the type of 12 well reservoir to use. The mastermix will be created in well A1. You may use the other wells as sources for reagents (slot 3 in the .csv)
</br>

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Tube racks](https://labware.opentrons.com/?category=tubeRack)
* [Aluminum blocks](https://labware.opentrons.com/?category=aluminumBlock)
* [12 well reservoirs](https://labware.opentrons.com/?category=reservoir)

### Pipettes
* [Single channel pipettes](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Pipette tips](https://shop.opentrons.com/universal-filter-tips/)

### Robot
* [OT-2](https://opentrons.com/ot-2)

### Reagents
* [Example reagents: NEB Taq PCR Kit](https://www.neb.com/products/e5000-taq-pcr-kit#Product%20Information)

*Note that you may use any reagent kit that you prefer with this protocol*

---

### Deck Setup
* Example setup

![Deck](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/generic_pcr_prep_1/example_deck.jpg)

![Reservoir](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/generic_pcr_prep_1/reservoir.jpg)


* Slot 1: Tube rack or well plate 1
* Slot 2: Tube rack or well plate 2
* Slot 3: 12-Channel reservoir: Well 1 - Mastermix target
* Slot 4: Tiprack for the left pipette
* Slot 5: Tiprack for the right pipette
* Slot 6: Empty
* Slot 7: Empty
* Slot 8: Empty
* Slot 9: Empty
* Slot 10: Empty
* Slot 11: Empty

---

### Protocol Steps
1. Select your parameters.
2. Upload your master mix CSV.
3. Download your protocol.
4. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
7. Hit "Run".
8. Robot will transfer each reagent from its source to well A1 of trough in slot 3.

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
generic_pcr_prep_1
