# STANDARD MP

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol performs a specific set of genealogy dilutions and transferred to and from 96 deepwell plates and 1.5ml, 15ml, and 50ml. Input for the protocol should be specified in a `.csv` file as shown in [this template](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3b3f1c/Alturas+Dilution+Temp+and+OT2+Pipette+Settings+332+312+V4.csv).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P300 and P1000 single-channel GEN2 electronic pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 300ul and 1000ul tiprack](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 4-in-1 tuberack sets](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with  [NEST 1.5ml snapcap, 15ml, and 50ml tubes](https://shop.opentrons.com/collections/verified-consumables)
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the number of samples to process, the mount side for your P300 multi-channel pipette, the volume of beads to transfer initially (in µl), and the bead separation time (in minutes).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3b3f1c
