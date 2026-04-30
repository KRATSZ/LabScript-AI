# 96-well Plasmid ezFilter Miniprep Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NUCLEIC ACID EXTRACTION & PURIFICATION
	* Nucleic Acid Purification

## Description
This protocol performs the [96-well Plasmid ezFilter Miniprep Kit](https://www.bioland-sci.com/index.php?main_page=product_info&products_id=137&zenid=6d2c9844db2a12e37e573e104fedbba5). For a detailed list of protocol steps, please see below.

Explanation of complex parameters below:
* `Number of plates`: Specify whether using 1 (slot 2 alone) or two (slots 2 and 5) plates for this run.
* `Number of Samples Plate 1 & 2`: Select the number of samples per plate. If the number of plates variable = 1 above, then the number of samples for plate 2 will be ignored.
* `P300 Mount`: Specify which mount (left or right) to host the P300 Multi-Channel Pipette

---

### Labware
* [NEST 1 Well Reservoir](https://shop.opentrons.com/consumables/)
* [Opentrons 300ul Tips](https://shop.opentrons.com/consumables/)
* [NEST 1 Well Reservoir](https://shop.opentrons.com/consumables/)
* USA Scientific 96 Deepwell Plate 2.4mL
* Custom 96 plates


### Pipettes
* [Opentrons P300 Multi-Channel Pipette](https://opentrons.com/pipettes/)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0a1784/Screen+Shot+2022-09-15+at+4.25.47+PM.png)

---

### Protocol Steps
1. Buffer A1 added to samples
2. Pause to swap plates and reagents (protocol pause specifies exact steps).
3. Buffer A2 added to samples.
4. Pause to swap plates and reagents (protocol pause specifies exact steps).
5. Buffer N3 added to samples.
6. Samples moved to plates 3 if one plate is selected, 3 and 6 if two plates are selected.
7. Pause to swap plates and reagents (protocol pause specifies exact steps).
8. Isopropanol added to samples and moved to new plate.
9. Wash buffer added to samples.
10. Elution buffer added to samples.

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
089108
