# Post RC-PCR Pooling of Nimagen SARS CoV-2 Library Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Pooling

## Description
This protocol performs the post RC-PCR pooling of the [Nimagen SARS CoV-2 Library Prep](https://www.nimagen.com/shop/products/rc-cov096/easyseq-sars-cov-2-novel-coronavirus-whole-genome-sequencing-kit). It has the option to pool samples from a variety of 384 well plates. The 384 well plate is divided into four quadrants and each quadrant can have up to 12 columns of samples, yielding a total of 48 columns worth of samples on a full plate.

![Quadrant Setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2bdff3/quadrant_diagram.png)

**Note:** The diagram above color coordinates the four quadrant positions. Each quadrant can take up to 12 columns worth of samples. The diagram above shows 1 column worth of samples.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons 200uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 20uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [4-titude FrameStar 384 Well Plate](https://www.thermofisher.com/order/catalog/product/95040450#/95040450)
* [BIOplastics 384 Well Plate](https://www.bioplastics.com/productdetails.aspx?code=B70515)
* [Eppendorf Twin.tec LoBind 384 Well](https://online-shop.eppendorf.co.uk/UK-en/Laboratory-Consumables-44512/Plates-44516/Eppendorf-twin.tec-PCR-Plates-LoBind-PF-58208.html#Accessory)
* [Eppendorf Twin.tec LoBind 96 Well](https://online-shop.eppendorf.co.uk/UK-en/Laboratory-Consumables-44512/Plates-44516/Eppendorf-twin.tec-PCR-Plates-LoBind-PF-58208.html#Accessory)
* [P300 Single Channel GEN2](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)
* [P20 Multichannel GEN2](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Setup**

![Deck Layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2bdff3/2bdff3_new_layout.png)

**Note: Slots 9, 10, 11 contain empty tip racks for the Opentrons 20 uL tips.**

**Protocol Steps**

1. Mix column in the 384 well donor plate, then transfer sample to the first column of the 96 well recipient plate. This step should proceed for all available columns in all four quadrants.
2. Mix well A1 and then transfer the total volume of samples in A1 of the 96 well recipient plate to the 1.5 mL Eppendorf tube in position A1 of the tube rack. This step should proceed for all wells in column 1 (A1-H1).

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

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
2bdff3