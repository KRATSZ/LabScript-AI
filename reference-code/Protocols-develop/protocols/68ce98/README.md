# Custom Plate Transfer

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol performs the transfer of samples and reagent from one plate to another. It will pre-wet the tip and aspirate/dispense 300uL 3 times. Then it will transfer 750 uL to a second plate with a 30uL air gap, blow out and touch tip at the destination.

---

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P300 multi-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Waters 2mL 96 Well Plate](https://www.waters.com/nextgen/us/en/shop/vials-containers--collection-plates/186002482-96-well-sample-collection-plate-2-ml-square-well-50-pk.html)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Waters 2mL 96 Well Plate (Slot 1)
* Waters 2mL 96 Well Plate (Slot 2)
* Opentrons 300uL Tip Rack (Slot 4)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the required parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
68ce98