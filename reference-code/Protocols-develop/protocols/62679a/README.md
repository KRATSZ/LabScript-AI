# Compound Dilution

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Serial Dilution

## Description
This protocol performs a compound plating and subsequent serial dilution for up to 36 stock compounds. Each compound's dilution will occupy a column of a 96-well plate, requiring up to 4x 96-well plates for a full 48-compound dilution protocol. Stock compound will be transferred to row A of the dilution plates, and a 6-step dilution will be carried down the plate through rows B-G. Well H of that column will contain pure DMSO. A P300 or P20 pipette is automatically selected for each compound's dilution, depending on the dilution factor, and thus, the transfer volume.

The input file for the workflow should be specified in a format similar to [this template](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/62679a/ex.csv).

---

### Labware
* [Greiner Bio-One 96-Wellplate V-Bottom 340µL, #651201](https://shop.gbo.com/en/usa/products/bioscience/microplates/96-well-microplates/96-well-polypropylene-microplates/651201.html)
* [PerkinElmer 96-Well StorPlate, U-Bottom 450µL, #6008190](https://www.perkinelmer.com/product/storplate-96-u-50-6008190)
* [Beckman Coulter 8-Channel Reservoir 19mL](https://www.beckman.com/supplies/reservoirs#product-table-wrapper) or [NEST 12-Well Reservoirs 15 mL #999-00076](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/62679a/deck2.png)

---

### Protocol Steps
1. Define number of compounds, volumes, order of compounds to transfer and desired final volume/dilution factor.
2. Pipette compound in Compound Management to mix before transferring contents to corresponding empty Compound Plate in the specified order.
3. Repeat Step 2 for all specified plates.
4. Pause to allow user to check plate/spin down to ensure there are no air bubbles.
5. Transfer desired amount of DMSO from reservoir to Compound plates starting from row B down to row H.
6. Transfer desired amount of compound to subsequent row depending on the dilution factor.
7. After transferring from the previous row, mix dilution.
8. Repeat Steps 6 and 7 using a multi or single channel to perform desired 6 serial dilutions.

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
62679a
