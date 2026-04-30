# COVID-19 Patient Sample Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Serial Dilution

## Description
This protocol performs preparation of COVID-19 patient samples into a 96 well King Fisher deep well plate for downstream applications. It also has a double extraction mode where each sample will get aliquoted twice for extraction downstream. 

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons 1000uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [KingFisher Deep Well Plate 2 mL](https://www.thermofisher.com/order/catalog/product/95040450#/95040450)
* [P1000 Multichannel GEN2](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549142557)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Protocol Steps**

**Single Extraction**
1. Transfer 200 uL (default) of patient sample from patient tube in deck slot 4 position A1 into well A1 of the KingFisher deep well plate.
2. Transfer 200 uL (default) of patient sample from patient tube in deck slot 4 position B1 into well B1 of the KingFisher deep well plate.
3. This process continues by going down the column for both tube racks and the deep well plate. Tube racks incremement based on slot number.

**Double Extraction**
1. Transfer 200 uL (default) of patient sample from patient tube in deck slot 4 position A1 into well A1 of the KingFisher deep well plate.
2. Transfer 200 uL (default) of patient sample from patient tube in deck slot 4 position A1 into well B1 of the KingFisher deep well plate.
3. Transfer 200 uL (default) of patient sample from patient tube in deck slot 4 position B1 into well C1 of the KingFisher deep well plate.
4. Transfer 200 uL (default) of patient sample from patient tube in deck slot 4 position B1 into well D1 of the KingFisher deep well plate.
5. This process will continue aliquoting the same patient sample twice and will do up to 47 patient samples per run.

**Note**: Samples are not aliquoted into wells G12 and H12. Those are reserved for controls.

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
6f2d9b