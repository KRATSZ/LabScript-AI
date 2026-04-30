# Tube Filling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Tube Filling

## Description
This protocol performs a custom tube filling protocol through transferring sample from custom 100ml tubes to custom test tubes.

Depth from the lip of the sample tube from which to aspirate, as well as aspiration and dispense flow rates, should be input as a .csv in the following format **including the header line**:

```
distance down tube to aspirate (in mm),aspiration speed (in ul/s), dispense speed (in ul/s)
20,100,100
20,100,100

```

Empty lines will be ignored. You can download a template for this .csv file [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/272c63/template.csv).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P1000 GEN2 single-channel pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549109789)
* [Opentrons 1000ul tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* Custom tubes and tuberacks

---

![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Transfer Scheme  
![transfer scheme](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/272c63/transfer_scheme.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the parameters for your protocol.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
272c63
