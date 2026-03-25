# Aliquoting

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Aliquoting

## Description

Links:
* [Random Aliquoting](./925d07-cp)
<br></br>
<br></br>
* [Plasmind Luciferase Assay](./925d07-pla)
<br></br>
<br></br>
* [QIAcuity Plate Transfer](./925d07-q)
<br></br>
<br></br>
* [PCR Prep](./925d07-v3)
<br></br>
<br></br>

This protocol performs a custom aliquoting procedure based on a randomly-generated 1-4 plate map. Enough volume to accommodate all 4 destination wells, including overage volume, is aspirated from the source well and distributed to all 4 destination wells. A new tip is obtained for each source-destination set. The layout is shown below:  

![map](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/925d07/map.png)

The proper pipette (P20 or P300) is selected automatically based on the input siRNA volume.

---

### Labware

* [Eppendorf V-bottom, Lo-Bind 96-well plates #0030603303](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Plates-44516/DNA-LoBind-Plates-PF-16858.html)
* [Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

### Pipettes
* [P300 Single GEN2 Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [P20 Single GEN2 Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

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
925d07
