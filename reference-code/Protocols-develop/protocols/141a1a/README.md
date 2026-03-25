# Cell-Free Gene Expression (TXTL) Test

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cell-Free Gene Expression


## Description
This protocol automates the cell-free gene expression test as outlined by users at TU Munich. See below:</br>
</br>
*This protocol sets up a cell-free gene expression experiment (TXTL test) in a 384-well plate. A TXTL sample is composed of cell extract (E), buffer (B), and a plasmid coding for the desired genes. The cell extract and buffer volume in each sample is fixed, the volume of plasmid in each sample depends on the plasmid stock concentration and the desired sample concentration of the plasmid. The final volume of 15µl is reached by adding nuclease-free water to the sample.*</br>
</br>
With the parameters, the user is able to test separate samples for different plasmids coding for the fluorescent proteins (ex. RFP, YFP, GFP and CFP) and measure up to 3 replicates for each of them. In addition, up to two blank samples containing E+B and water are made. First, mastermixes of plasmid and water are made, then distributed to the corresponding wells in the 384-well plate. Then E+B mixes are prepared and also distributed to the corresponding wells.</br>
</br>
This protocol uses a custom labware definition for the Brand 384-well plate. When downloading the protocol, the labware definition (a JSON file) will be included for use with this protocol. For more information on using custom labware on the OT-2, please see this article: [Using labware in your protocols](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols)</br>
</br>
In the case that the protocol needs more tips than can be accommodated, the robot will pause, flash the rail lights, and ask the user to replace the tiprack.



---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 (GEN2) Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons P20 (GEN2) Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* (2) [Opentrons 4-in-1 Tube Rack Set, with 24-well top](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [1.5mL Centrifuge Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* [2mL Centrifuge Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-2-0-ml-microcentrifuge-tubes)
* [96-Well Aluminum Block](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set)
* PCR Strips
* Brand 384-Well Plate
* Reagents



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Brand 384-Well Plate

Slot 2: [Opentrons 4-in-1 Tube Rack Set, with 24-well top](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [1.5mL Centrifuge Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes) (for Cell Extracts + Buffer)

Slot 3: [96-Well Aluminum Block](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set) with PCR Strips (containing Buffer aliquots)

Slot 5: [Opentrons 4-in-1 Tube Rack Set, with 24-well top](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [2mL Centrifuge Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-2-0-ml-microcentrifuge-tubes) (for Plasmid stock and Nuclease-Free Water)
* A1: Plasmid 1 Stock (RFP)
* B1: Plasmid 2 Stock (YFP)
* C1: Plasmid 3 Stock (GFP)
* D1: Plasmid 4 Stock (CFP)
* A3: (Empty) Plasmid 1 Master Mix
* B3: (Empty) Plasmid 2 Master Mix
* C3: (Empty) Plasmid 3 Master Mix
* D3: (Empty) Plasmid 4 Master Mix
* A5: Nuclease-Free Water
* D5: (Empty) Pooled Buffer

Slot 6: [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

Slot 9: [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 7/8/10/11: [Opentrons Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)
</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Plasmid Mix CSV**: Upload a CSV containing headers (plasmid, molecular weight, concentration, and sample concentration).
* **Number of Replicates (1-3)**: The number of replicates per plasmid.
* **Number of Cell Extracts (1-24)**: The number of cell extracts (each extract will be dispensed in a column (1-24)).
* **Number of Blanks per Cell Extract (1, 2)**: The number of blanks (no plasmid) per cell extract (either 1 or 2).
* **P20 Mount**: Select which mount (left or right) the P20 Single is attached to.
* **P300 Mount**: Select which mount (left or right) the P300 Single is attached to.



### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol package containing the custom labware definition for the 384-well plate.
2. Upload the labware definition in the [OT App](https://opentrons.com/ot-app). For help, please see [this article](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
141a1a
