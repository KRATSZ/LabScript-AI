# Cherrypicking from .csv

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Featured
	* Cherrypicking

## Description
This protocol performs a custom cherrypicking workflow from a .csv file using custom Biotix filtertips. This protocol also performs a mix step after transferring liquid (3 repetitions) with the ability to specify the aspirate and dispense height from the top of the source and destination wells.



Explanation of complex parameters below:

* `input .csv file`: Here, you should upload a .csv file formatted in the [following way](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2c81c0/csv_template.csv), being sure to include the header line. Note that `source labware` and `destination labware` must be either `plate`, `tuberack`, or `deepplate`, which will be considered as the Bio-Rad 200ul plate, Opentrons 24 Eppendorf 1.5mL safelock snapcap tube rack, and the Nest 96 Deepwell Plate 2mL respectively. A value of 0 for the `Height Offset` columns returns the top of the well.
* `P10 GEN1 single-channel pipette mount`: Specify which mount (left or right) to load the P10 GEN1 Single Channel pipette.
* `P300 GEN1 single-channel pipette mount`: Specify which mount (left or right) to load the P300 GEN1 Single Channel pipette.
* `Change Tips`: Specify whether the pipette should have a new tip either once per well transfer or in between well transfers.

---

### Labware
* [Bio-Rad Hard-Shell® 96-Well PCR Plates 200µl #HSP9601](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [NEST 96 Deepwell Plate 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep)
* [Opentrons P10 GEN1 single-channel pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons P300 GEN1 single-channel pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Biotix 96 Filter Tiprack 10µl](https://biotix.com/products/utip-for-universal-pipettes/10-%ce%bcl-xl-racked-filtered-sterilized/)
* [Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://labware.opentrons.com/opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap?category=tubeRack)

### Pipettes
* P10 Single Channel Pipette GEN1
* P300 Single Channel Pipette GEN1


---

### Deck Setup
* Example deck layout. Biotix and Opentrons tips should always be in below slots. Source and Destination labware and slots can be specified in the CSV.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2c81c0/Screen+Shot+2021-04-30+at+3.31.52+PM.png)
---

### Protocol Steps
1. Pipette will aspirate a user-specified volume at the designated labware and well according to the imported csv file. Slot is also specified, as well as aspiration height from the top of the well.
2. Pipette will dispense this volume into user-specified labware and well according to the imported csv file. Slot is also specified, as well as dispense height from the top of the well.
3. Mix step with user-specified volume for 3 repetitions.
4. Steps 1, 2, and 3 repeated over the duration of the CSV.

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
2c81c0
