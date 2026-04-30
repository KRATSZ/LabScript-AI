# DNA Extraction with Heater Shaker - Part 2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* DNA Extraction

## Description
This protocol performs a DNA extraction with the samples gathered from part 1 of the protocol. For specific protocol steps, please see below. A field for aspiration height when transferring the samples from the heater shaker to the magnetic module allows the user to ensure beads are not picked up, and and aspiration rate of 10% of the default is instilled to ensure so. Note: for reagent 4 in columns 4 & 5, reagent 5 in columns 6 & 7, and reagent 6 in columns 8 & 9, split the total calculated reagent volume EQUALLY between the pair of columns, as the protocol will circle between the pair of columns as the source.



---

### Modules
* [Heater-Shaker Module](https://shop.opentrons.com/heater-shaker-module/)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [Abgene 96 deep well plate](https://assets.fishersci.com/TFS-Assets/LCD/Datasheets/Abgene-96-Well-Plate-Datasheet.pdf)
* [Opentrons 200ul Filter Tips](https://shop.opentrons.com/universal-filter-tips/)

### Pipettes
* [P300 Single Channel Pipette](https://opentrons.com/pipettes/)
* [P300 Multi Channel Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0530d8/Screen+Shot+2022-11-07+at+11.05.05+AM.png)

### Reagent Setup
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0530d8/Screen+Shot+2022-11-01+at+11.46.43+AM.png)

---

### Protocol Steps
1. Samples + controls transferred to magnetic module
2. Adding 240ul of reagent in column 4 of the reagent plate
3. Remove supernatant
4. Two washes with columns 5 and 6 of the reagent plate
5. 30ul reagent added to samples and controls from column 7 of reagent plate
6. Samples + controls moved to fresh plate


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
0530d8-pt2
