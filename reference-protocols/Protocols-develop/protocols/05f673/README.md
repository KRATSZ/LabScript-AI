# Cell Normalization

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization


## Description
This protocol allows for a robust cherrypicking and normalization in one step.</br>
</br>
Using a [P1000 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette), buffer will be transferred to all wells specified in the **Normalization CSV** (see below), before transferring samples from up to four source plates to four destination plates (specific plate and well location specifed in **Normalization CSV**).</br>
</br>
The .csv file should be formatted as shown in the example below, **including headers**:

```
Source Plate, Source Well, Dest Plate, Dest Well, Buffer Volume (in ul), Culture Volume (in ul)
2,A1,1,A1,1591,1870
2,B1,2,B1,1629,808
```

</br>
**Update**: This protocol has been updated per user request and now allows for the option to use 96-well plates and (if using 96-well plates), prefill the plates with a [P300 8-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette).</br>
Explanation of complex parameters below:
* **P1000 (GEN2) Mount**: Specify whether the P1000 single channel pipette is on the left or right mount.
* **Normalization CSV**: CSV containing transfer information for normalization (as outlined above).
* **Labware Type**: Select between Corning 24-Well Plate and Corning 96-Well Plate.
* **Prefill Volume**: Specify the volume (in µL) to prefill the 96-Well plates.


---


### Labware
[Corning 24-Well Plate, 3.4mL, Flat](https://labware.opentrons.com/corning_24_wellplate_3.4ml_flat?category=wellPlate) or [Corning 96-Well Plate, 360µL, Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)</br>
[Agilent 1-Well Reservoir, 290mL](https://labware.opentrons.com/agilent_1_reservoir_290ml?category=reservoir)</br>
[Opentrons 1000uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)</br>
[Opentrons 300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips), optional</br>

### Pipettes
* [P1000 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P300 8-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette), optional

---

### Deck Setup
Source plates containing samples can be placed in deck slots 1, 2, 3, and 5 (and should be referred to as 1-4 in the CSV). Destination plates (where buffer and cells will be added) can be placed in deck slots 6, 8, 9, and 11 (and should be referred to as 1-4 in the CSV). Tips should be placed in deck slot 7.

---

### Protocol Steps
1. User-specified amounts of Buffer (column E) are transferred to all **destination wells** (column D), using a single tip.
2. After all of the Buffer transfers, the tip is dropped in the trash bin and the following occurs for each row in the CSV ~
3. A new tip is picked up.
4. **Culture Volume** (column F) is transferred from **Source Well** (column B) of **Source Plate** (column A) to **Dest Well** (column D) of **Dest Plate** (column C) after mixing three times in the source well.
5. The tip is dropped in the waste bin.
6. The protocol is complete.


## Process
1. Input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
05f673
