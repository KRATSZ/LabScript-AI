# Saliva sample transfer from tuberacks to 96 well plate

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* PCR prep

## Description
This protocol transfers saliva samples from 25 mL tubes to a 96 well plate. The samples are located in 6 4-in-4 tube racks on the left side of the deck. Optionally a second set of tube racks can replace the first one if more than 45 samples need to be distributed. Optionally the target plate can be placed on a temperature module with an aluminum block.

The destination plate is divided into four quadrants and the samples are distributed in a zig zag pattern from top left - top right - bottom left - bottom right (see below). Samples are not transferred to the three first wells of the target plate because they contain control samples, symmetrically the first 3 tube slots in Sample set 1:Tuberack quadrant 1 contain no sample tubes.

The tubes in the tuberacks in slot 10, 11, 7 and 8 constitute the 1st tuberack quadrant, and should be regarded as a single unit (Tuberack quadrant 1) consisting of 4 rows of tubes with 12 columns. Samples are transferred in row order to quadrant 1 of the target plate for Sample set 1, and to quadrant 3 for Sample set 2.

Similarly the tuberacks in slot 4, 5, 1 and 2 constitute Tuberack quadrant 2. Samples from Sample set 1 in Tuberack quadrant 2 are transferred to Target quadrant 2, and samples from Sample set 2 are transferred to Target quadrant 4.

**96 well-plate layout**
```
Target quadrant 1 (top left)
A1-D1 to A6-D6 (A1-A3 are unused)

Target quadrant 2 (top right)
A7-D7 to A12-D12

Target quadrant 3 (bottom left)
E1-H1 to E6-H6

Target quadrant 4 (bottom right)
E7-H7 to E12-H12
```

Explanation of parameters below:
* `Is there a first set of tubes?`: Is there a first set of tubes? (Sometimes the user may have already transferred the first set of tubes and wants the protocol to run from the second set of tuberack samples)
* `Number of tubes/samples in the first set of tubes`: How many tubes there are in the first set of tube racks. These samples will be transferred to quadrant 1 (and 2) of the destination plate
* `Is there a second set of tubes?`: Whether to pause the protocol so that a second set of tube racks can be loaded onto the deck
* `Number of tubes/samples in the second set of tubes`: How many samples there are in the second set of tuberacks (Only needs to be set if a second set of tube racks is loaded)
* `Sample volume (µL) to aspirate`: Volume of sample to transfer (5 or 50 µL). This parameter controls which pipette and tiprack is used: 5 uL means that the 20 uL pipette will be used in in the right mount, and that the pipette tips should be filtered 20 uL tips. 50 uL means that the 300 uL pipette will be used in the left mount along with 200 uL filter tips.
* `Aspiration flow rate (µL/s)`: rate of aspiration in microliters per second
* `Dispension flow rate (µL/s)`: rate of dispension in microliters per second
* `Aspiration height from the bottom of the tubes (mm)`: Height from the bottom of the tubes to aspirate from in mm
* `Dispension height from the bottom of the tubes (mm)`: Height from the bottom of the plate wells to dispense from in mm
* `(Optional) Temperature module with aluminum block`: Parameter to indicate whether you are using a temperature module with an aluminum block to put your target plate on
* `Set temperature of the temperature module`: Temperature to set on the temperature module in degrees C
* `Amount of time to keep the pipette in the tube after aspiration (s)`: How many seconds to wait before withdrawing the pipette from the tube after aspiration

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [4-in-1 tube racks](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Stellar Scientific 96 well plate](https://www.stellarscientific.com/96-well-low-profile-fast-type-pcr-plate-with-raised-rim-edge-0-1ml-rnase-and-dnase-free-clear-100-cs/)

### Pipettes
* [20 µL single-channel pipette gen2](https://shop.opentrons.com/single-channel-electronic-pipette-p20/) - Load in the right mount
* [300 µL single-channel pipette gen2](https://shop.opentrons.com/single-channel-electronic-pipette-p20/) - Load in the left mount
* [20 µL filter tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/) - When the sample volume is 5 uL
* [200 µL filter tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/) - When the sample volume is 50 uL

Note that there is only one tiprack that goes into slot 9 per run which is determined by the sample volume.

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/300073/deck.jpg)

---

### Protocol Steps
1. If a temperature module is on the deck the first step is to set the temperature according to the parameter.
2. Samples are transferred from the first set of tubes to the destination plate
3. If a second set of tuberacks are designated the protocol pauses and allows the user to switch out the tube racks before continuing.
4. The second set of samples is transferred from the tubes to the destination plate

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
300073
