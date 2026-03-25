# Protein Array

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
    * Assay

## Description
This protocol performs a protein array on ONCYTE SuperNOVA slides mounted on an Inheco Teleshake 1536 using a P300 multi-channel pipette. For reagent setup in the 12-channel reservoir, see 'Additional Notes' below. Note that the user is prompted three times to engage and disengage the shaker (mounted on the deck). The Teleshake with slides will occupy slots 1, 2, 4, and 5, and will be calibrated from slot 4.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Grace ONCYTE SuperNOVA 16-well slides #705116](https://gracebio.com/product/oncyte-supernova-705116/)
* Custom 4-slide adapter for Inheco Teleshake 1536 (each slide with 8x2 square wells)
* [Bio-Rad Hard Shell 96-Well PCR plate 200ul #hsp9601 (if automatically adding samples)](http://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Agilent 1-Well Reservoir 290mL #201252-100](https://www.agilent.com/store/en_US/Prod-201252-100/201252-100)
* [USA Scientific 12-Well Reservoir 22mL #1061-8150](https://www.usascientific.com/12-channel-automation-reservoir.aspx)
* [Opentrons P300 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 300ul pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips?variant=15954632802398)
* [Inheco Teleshake 1536](https://www.inheco.com/fileadmin/web_data/Downloads/Data-Sheets/Shaker.pdf)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

12-channel reservoir
* Super G plus blocking buffer: channel 1
* Secondary antibody: channel 2
* PBST: channels 3-6
* Super G: channel 7

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the mount for your P300 multi-channel pipette, the number of slides to process (1-4), and the manner of sample addition (manual or automatic).
2. Download your protocol package.
3. Upload your custom labware and protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2). **Ensure that you calibrate your slides mounted on the Teleshake to the precise location from which you would like to aspirate liquid.**
6. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
56a6a1
