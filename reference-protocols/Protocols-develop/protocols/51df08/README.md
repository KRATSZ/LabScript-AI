# Mass Spec Sample Prep on Custom Slide

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
    * Assay

## Description
This protocol performs a mass spec sample prep on up to 10 samples with up to 5 antibodies on up to 2 custom 72-sample slide mounts (the top row of 9 wells are left blank). Samples and antibodies should be loaded in their respective tuberacks down the columns and then across the rows. Samples and antibodies are filled in the slides down the first column of each slide, then up the second, and finally down the third column. For more detailed sample and reagent setup, please see below.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* custom 3-grid 3x8 slide mount
* [Opentrons 4x6 tuberack insert](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 1.5ml Eppendorf snapcap tubes
* [Opentrons 2x3 tuberack insert](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 50ml Falcon tubes
* [Opentrons 20ul pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 300ul pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips?variant=15954632802398)
* [Opentrons P20- and P300-single GEN2 electronic pipettes](https://shop.opentrons.com/collections/ot-2-pipettes)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

2x3 50ml tuberack (slot 1)
* detergent wash buffer: tube A1
* BSA blocking buffer: tube B1
* PBS: tubes A2-B2
* water: tubes A3-B3

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the respective numbers of samples and antibodies, and the respective mount sides for your P20 and P300 pipettes.
2. Download your protocol package.
3. Upload your custom labware and protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
51df08
