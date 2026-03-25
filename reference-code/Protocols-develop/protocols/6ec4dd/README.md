# NGS Library Prep Part 1: PCR Setup I

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs part 1 of a custom NGS library prep workflow: PCR Prep 1.

Explanation of complex parameters below:
* `track tips across protocol runs`: If set to `yes`, tip racks will be assumed to be in the same state that they were in the previous run. For example, if one completed protocol run accessed tips through column 5 of the 3rd tiprack, the next run will access tips starting at column 6 of the 3rd tiprack. If set to `no`, tips will be picked up from column 1 of the 1st tiprack.

---

### Labware
* [Bio-Rad Hard-Shell® 96-Well PCR Plates, high profile, semi skirted, clear/clear #HSS9601](https://www.bio-rad.com/en-us/sku/hss9601-hard-shell-96-well-pcr-plates-high-profile-semi-skirted-clear-clear?ID=hss9601)
* [ThermoFisher KingFisher 96-Well Plate,s 200 μL #97002540B](https://www.thermofisher.com/order/catalog/product/97002540?SID=srch-srp-97002540#/97002540?SID=srch-srp-97002540)
* [Opentrons 20µl tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

### Pipettes
* [Opentrons P20 Multi-Channel GEN2 Electronic Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

---

### Deck Setup
![deck setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6ec4dd/deck_setup.png)  
blue: initial samples  
green: mastermix (180µl per well)

---

### Protocol Steps
1. 15µl of mastermix is pre-added from the first column of the reagent plate to all wells of the PCR plate using the same set of tips.
2. 10µl of each sample is transferred from the sample plate to the corresponding well of the PCR plate with pre-added mastermix. New tips are used for each transfer.

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
6ec4dd
