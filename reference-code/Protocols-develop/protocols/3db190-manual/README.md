# PCR/qPCR Prep (Manual Prep)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol automates certain steps of the Lyra Direct SARS-CoV Assay. This protocol assumes buffer is being added manually. The automated steps include mixing of the deep well block, and transferring samples to the PCR plate. 

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P20 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [P1000 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 20ul filter tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-filter-tip)
* [Opentrons 1000ul filter tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips)
* [MicroAmp™ EnduraPlate™ Optical 96-Well PCR Plates](https://www.thermofisher.com/order/catalog/product/4483354#/4483354)
* [Eppendorf 96 Deep Well Block 1000ul](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Plates-44516/Eppendorf-Deepwell-Plates-PF-55960.html)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Deck Setup
* Opentrons 1000ul filter tiprack (Slot 4)
* Opentrons 20ul filter tiprack (Slot 7)
* Eppendorf 96 Deep Well Block 1000ul (Slot 2)
* MicroAmp™ EnduraPlate™ Optical 96-Well PCR Plate (Slot 3, should be rested on top of the Eppendorf cooling block)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the total sample number (including controls, For Example: if you have 38 patient samples and 2 controls, you would enter 40), select P20-single channel mount, and select P1000-single channel mount
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3db190