# Temperature Controlled PCR Prep With Tube Strips

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol distributes reliance One Step Mulitplex RT-qPCR supermix to each well on a cool (4C) 96 well plate. After, saliva samples from custom Opentrons tube racks are distributed to each well containing mastermix, with a mix step to follow.

Explanation of complex parameters below:
* `Number of columns`: Specify the number of samples (wholly divisible by 8) that the OT-2 will distribute mastermix to on the 96 well plate (1-96).
* `Delay after aspiration`: Specify the number of seconds after aspirating for the pipette to pause to achieve full volumes.
* `Mix repetitions`: Specify the number of times to mix the mastermix and saliva.
* `Tube Aspiration Height`: Specify the aspiration height from the bottom of the tube (in mm) to aspirate from when transferring saliva in the final step.
* `Tube-Strip Aspiration Height for Multi Channel`: Specify the aspiration height from the bottom of the tube strip that the multi-channel pipette visits.
* `Aspiration/Dispense Rate`: Specify the aspiration/dispense rate for the single and multi-channel pipettes. A value of 1 returns the default speed, 0.5 would return half of the default speed, etc. 
* `P20 Multi GEN2 Mount`: Specify the mount (left or right) of the P20 Multi GEN2 Pipette.
* `P20 Single GEN2 Mount`: Specify the mount (left or right) of the P20 single GEN2 Pipette.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Biorad 96 well plate 200ul](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* PCR tube strips
* Opentrons custom 4x6 3D printed tube racks

### Pipettes
* [P20 GEN2 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P20 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Reagents
* Reliance One Step Mulitplex RT-qPCR supermix
* Eurofins genomics Saliva Direct primer and probe set

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3b0db0/Screen+Shot+2021-06-03+at+11.14.47+AM.png)

### Reagent Setup

PCR tube strips should be placed in the first four columns of the well plate on slot 4. The first PCR tube strip (column 1 on slot 4) is responsible for providing mastermix to 3 columns of the well plate on slot 1. Columns 4-6 of the well plate on slot 1 are populated with the PCR strip in column 2 on slot 4, and so on and so forth. Note, if the number of samples is not divisible by 8 (not full columns), the protocol will switch to using the P20 to populate the last unfilled column.The P20 single channel pipette will access mastermix from PCR tubes A1, B1, C1... and so on (starting from first PCR strip).

Saliva tube samples should be placed by column (A1, B1, etc.) starting from tube rack 1 on slot 2. The OT-2 will do 1-to-1 tube to well transfers by column, with one tube rack completely picked before moving on (tube racks move in order from slot 5 to slot 11).

---

### Protocol Steps
1. Mastermix is distributed to the plate (same tip).
2. Saliva is added to the mastermix and mixed (change tip).

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
3b0db0
