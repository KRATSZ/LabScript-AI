# Drop Casting Polymer to Silicon Wafer

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol drop casts a mixed solution of polymer to a silicon wafer. The protocol can be broken down into the following parts:

* Mix 3 user-specified volumes (via CSV) of polymer in a mix plate.
* Mix solutions, drop cast 1-1 transfer from mix plate onto silicon wafer.

 The protocol begins by mixing 3 solutions of polymer (volumes of each respective solution specified by the user via a CSV file) in a 96 well plate, up to the number of samples specified. After a mix step, solutions are transferred 1-to-1 from the 96 well plate to the silicon wafer (A1 to A1, B1 to B1, etc.). The silicon wafer is treated as a 24, 48, or 96 well grid for this step, although in reality the surface is uniform.

 The option to have various grid sizes is to vary spacing between drops. Depending on the solution volume, viscosity, dispense flow rate, and dispense height above the wafer, an appropriate grid can be chosen.  

Explanation of complex parameters below:
* `Number of Samples`: Specify how many samples will be transferred onto the silicon wafer (number of wells).
* `CSV`: Upload a CSV which specifies transfer volumes of the three solutions to be mixed and added to the silicon wafer.
The CSV should be formatted like so:

`Well` | `Transfer Volume Solution 1 (ul)` | `Transfer Volume Solution 2 (ul)` | `Transfer Volume Solution 3 (ul)` | `Transfer Volume to Silicon Plate (ul)`

Example Row: `A1`, `5`, `10`, `3`, `18`

The first row should contain headers (like above). All following rows should just include necessary information. </br>

Samples will be referenced in this protocol, as well as referenced in the CSV in order by column (e.g. A1, B1, C1, etc.) up to the number of samples for the run. The first `Well` column in the CSV should thus be ordered, A1, B1, C1, etc. </br>
* `Dispense Height Above Wafer`: Specify the height above the wafer to dispense mixed solution. **Caution:** a value of 0 returns the top of the wafer, with a value of 1 returning 1mm above the top of the wafer, for example. Negative numbers can also be passed (distance from top of the wafer) - use discretion to avoid tip crashing.
* `Dispense Flow Rate`: Specify the dispense flow rate of solution onto the silicon wafer.
* `Mix Repetitions`: Specify the number of times each well will be mixed in the mix well plate before being transferred onto the wafer.
* `Mix Volume`: Specify the volume at which each well be mixed.
* `Initial Volume in Solution`: Specify the initial volumes in all 3 tubes. This parameter is used for liquid tracking and ensuring the pipette is not submerged in solution.
* `Delay after dispense before returning tip`: Specify the amount of time (in seconds) before the tip is returned to the tip rack after dispense. Following the dispense, there will be a delay, then blow out and touch tip. 
* `P20 Single Mount`: Specify which mount the P20 is on (left or right).

---

### Modules
* No modules are required for this protocol.

### Labware
* [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)
* [Costar 96 Well Plate](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)
* Silicon Wafer with Opentrons Labware Adapter
* Custom 8-tube 20ml tube rack

### Pipettes
* [P20 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)


---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4d9b8b/Screen+Shot+2021-04-20+at+7.36.37+AM.png)

### Reagent Setup
* Custom 8-tube 20ml tube rack with solutions in A1, A2, and A3.

---

### Protocol Steps
1. Transfer between 0-20 uL of solution 1 (tube A1) to well A1. return tip.
2. Transfer between 0-20 uL of solution 2 (tube A2) to well A1. return tip.
3. Transfer between 0-20 uL of solution 3 (tube A3) to well A2. return tip.
4. Mix Well A1 with new tip.
5. Extract between 0-20 uL of well A1 solution and deposit on silicon wafer in position A1,
6. Dispose of tip
... Repeat this process up to 96 times, each successive iteration mixing in a new well (A2, A3, A4...) and depositing in the next location on the Silicon Wafer (A2, A3, A4)

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
4d9b8b
