# RNA Quantitation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* Complete PCR Workflow

## Description
This protocol reformats RNA into a 96-well plate per a .csv input. Up to 96 tubes can be reformatted, and fresh tips are granted between each tube. Volume, source slot, source well, destination slot and destination well are all information that is taken from the csv to perform the protocol. Note: the csv format is NOT the same for [Part 2](https://protocols.opentrons.com/protocol/7ada78-pt2). For csv information and formatting notes, see below.


Explanation of complex parameters below:
* `.CSV File`: Here, you should upload a .csv file formatted in the following way, being sure to include the header line (use slot 7 for the thermocycler slot, and input an "x" for values that are not needed in that row):
![csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7ada78/pt1/Screen+Shot+2022-01-25+at+11.16.36+AM.png)

If using a kingfisher plate, the multi-channel pipette will be used. For destination well, include only wells in the first row (A1, A2, A3,.., A12). The protocol will then proceed to perform full column transfers of the volume specified, for all columns specified (feel free to skip columns).
* `Pipette Mount`: Specify which mount (left or right) to host the P20 single and multi-channel pipettes, respectively.

---

### Modules
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)


### Labware
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/verified-labware/well-plates/)
* [Opentrons 4-in-1 tube rack with 1.5mL Eppendorf snap cap tubes](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Opentrons 20ul Filter tips](https://shop.opentrons.com/universal-filter-tips/)
* 96-W OptiPlate
* 96-W Kingfisher plate

### Pipettes
* [P20 Single-Channel Pipette](https://opentrons.com/pipettes/)
* [P20 Multi-Channel Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7ada78/pt1/Screen+Shot+2021-12-22+at+5.23.33+PM.png)

---

### Protocol Steps
1. Use single channel to transfer x uL (x = 1 to 20) of samples from tubes to corresponding well of 96-well plate (e.g. slot 4 A1 => slot 3 well A1, slot 2 A1 => slot 3 well E7).
2. Repeat step 1 for all samples (up to 96).

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
7ada78-pt2
