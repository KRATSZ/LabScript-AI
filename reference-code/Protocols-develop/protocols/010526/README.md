# Restriction Digests

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Restriction Digest

## Description
This protocol performs restriction digests on a multitude of samples using various [restriction enzymes](https://www.neb.com/products/restriction-endonucleases/restriction-endonucleases?gclid=EAIaIQobChMInsuBgInC8QIVeXxvBB06IAdAEAAYASAAEgIWHvD_BwE) and then performs an incubation on the thermocycler module for heat inactivation. The sample data is inserted using a CSV file which contains the necessary data to load enzymes, transfer reagents and location details. An example of the CSV file can be downloaded [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/010526/Table1.csv).

Explanation of complex parameters below:
* `P20 Single Channel GEN2 Mount Position`: The position your pipette is mounted on the OT-2 (Left or Right).
* `P300 Single Channel GEN2 Mount Position`: The position your pipette is mounted on the OT-2 (Left or Right).
* `Samples Labware Type`: The type of labware used to hold your samples. You have the option to use 2x 24-well tuberacks (Slot 2 and 4) OR 1x 96-well NEST 100 uL PCR Plate (Slot 2).
* `Input CSV File`: The input CSV file containing your sample data. You can download an example CSV file [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/010526/Table1.csv) or use the following formatting:
```
UID,ng/ul,800ng (ul),Water (ul),Enzyme,Location
1301-1,328,2,33,EcoRI,A1
1301-2,250,3,32,EcoRI,A2
1301-3,180,4,31,EcoRI,A3
1303-1,145,6,29,EcoRI,A4
1303-2,169,5,30,EcoRI,A5
1303-3,162,5,30,EcoRI,A6
1362-1,150,5,30,BamHI; HindIII,A7
1362-2,156,5,30,BamHI; HindIII,A8
1362-3,231,3,32,BamHI; HindIII,A9
1368-1,67,12,23,BamHI; HindIII,A10
1368-2,183,4,31,BamHI; HindIII,A11
1368-3,231,3,32,BamHI; HindIII,A12
```
* `Temperature Module Hold Temperature (C)`: The temperature the temperature module should reach and hold to keep reagents cool. 
* `Reaction Volume (uL)`: Total reaction volume for all samples in microliters (uL).
* `Enzyme Volume (uL)`: The enzyme volume used for individual enzyme transfers to the sample wells in microliters (uL).
* `Enzyme Transfer Aspirate Flow Rate (uL/s)`: The aspirate flow rate for the enzyme transfer step in microliters/second (uL/s).
* `Enzyme Transfer Dispense Flow Rate (uL/s)`: The dispense flow rate for the enzyme transfer step in microliters/second (uL/s).
* `Digest Duration (s)`: The total duration in seconds for the incubation at 37°C.
* `Heat Kill Temperature (°C)`: The temperature for heat inactivation (default: 65°C).
* `Heat Kill Duration (s)`: The duration in seconds for heat kill (default: 1200).

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Labware
* [4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Aluminum Block Set](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons Pipette Tips](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [P20 Single Channel GEN2](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)
* [P300 Single Channel GEN2](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)

### Reagents
* [NEB Restriction Enzymes](https://www.neb.com/products/restriction-endonucleases/restriction-endonucleases?gclid=EAIaIQobChMInsuBgInC8QIVeXxvBB06IAdAEAAYASAAEgIWHvD_BwE)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/010526/010526_layout.png)

**Note: If you set `Samples Labware Type` to `1x 96 Well PCR Plate` only a 96 Well PCR plate should be placed in Slot 2.**

### Reagent Setup
* Samples: Place samples in order going down the column in both labware types. For the tuberack you must fill in the first tuberack before moving onto the second one.
* Buffer: Place in position **D6** on Temperature Module
* Water: Place in positions **D1** and **D2** on Temperature Module

**Enzyme Setup**

* Enzymes should be placed in alphabetical order on the Temperature Module. **Note: Enzymes should NOT be placed in Row D.**

**Example:**

![Enzyme Setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/010526/enzyme_setup.png)

---

### Protocol Steps
1. Set Temperature Module to 4°C.
2. Pause protocol for loading enzymes into the Temperature Module.
3. Set Thermocycler Block Temperature to 4°C and Hold.
4. Transfer Water to PCR Plate in Thermocycler.
5. Transfer Buffer to PCR Plate in Thermocycler.
6. Transfer Samples to PCR Plate in Thermocycler with a 2x Mix at 20 uL Volume (tips changed between transfers).
7. Transfer enzymes to PCR Plate in Thermocycler with a 6x Mix at 20 uL (tips changed after mix step).
8. Thermocycler Incubation Step (contains variables):
* Set Block Temperature to 37°C for X seconds
* Heat Lid to 70°C 
* Set Block Temperature to Heat Kill Temperature for X seconds.
* Set Block Temperature to 4°C and Hold.


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
010526