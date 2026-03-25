# OT-2 Demo

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Getting Started
	* OT-2 Demo

## Description
Learn the function OT-2 quickly! This simple plating protocol shows the flexibility of custom protocols hosted on our Protocol Library.

Reagents are transferred down columns and then across rows as shown here.  
![order](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/demo/order.png)  

If the source labware is selected to be a 24x tuberack, reagents will be transferred in quadrupliate (ex: reagent tube A1 to destination labware wells A1-D1, reagent tube B1 to destination labware wells E1-H1, reagent tube C1 to destination labware wells A2-D2, etc.)

If the source labware is selected to be a 12-channel reservoir, reagents will be transferred column to column (ex: reservoir channel 1 to destination labware column 1, reservoir channel 2 to destination labware column 2, etc.)

---
### Modules
* [Opentrons Magnetic Module GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [NEST 12 Well Reservoir 15 mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [NEST 96 Well Plate 200 µL Flat](https://shop.opentrons.com/collections/verified-labware/products/nest-96-well-cell-culture-plate)
* [Opentrons 4x6 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with Eppendorf 2 mL Safe-Lock Snapcap
* Any [Opentrons 96 tiprack](https://shop.opentrons.com/collections/opentrons-tips) depending on what pipette is selected.

### Pipettes
* Any [Opentrons single-channel GEN2 pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) can be used in this protocol.
* Any [Opentrons multi-channel GEN2 pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) can be used in this protocol.

---

### Deck Setup
Here's an example deck setup (note that this will vary based on your selected parameters below):  
![deck setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/demo/deck_setup.png)

### Reagent Setup
* Place your reagent arranged down the rows and then across the columns of your source labware.

---

### Protocol Steps
1. Reagents are transferred sequentially from the source labware to the corresponding positions of the destination labware.
2. If you are using the magnetic module, the module engages 18mm.
3. The protocol finishes execution and prompts the user for next steps.

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
demo
