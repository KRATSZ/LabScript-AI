# Urine Toxicology Using Enzyme Hydrolysis

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps a 96 well plate with urine and enzyme hydrolysis, as well as trichloroacetic acid and dilution buffer. The urine samples in the 4 tube racks exactly mimic the 96 well plate with 15 controls already put in by column. The sample pick-off begins from D2 in the tuberack on slot one, corresponding to H2 of the well plate in slot 3 for dispensing. Delays and pauses are included in the protocol to allow for incubation periods and mix steps.

Explanation of complex parameters below:
* `Use csv for this run?`: Specify whether a csv file will be uploaded for this run. If not, nothing in `.CSV File` below will be referenced.
* `.CSV File`: Upload the csv file for this run. The csv file will map which samples the pipette will visit the bottom of the tube. Wells marked with `X` will be aspirated from the `Sample Aspiration Height` parameter (see below). Otherwise, wells marked with `O` (capital letter O, not zero) will be aspirated from the bottom of the tube. Refer to the csv sample below.
![csv sample](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1dfebe/Screen+Shot+2021-10-20+at+11.52.43+AM.png)
* `Number of Samples`: Specify the number of samples (1-81) for this run.
* `Tip Withdrawal Speed`: Specify the tip withdrawal speed for the tip to leave the urine samples.
* `Sample Aspiration Height (mm)`:  Specify the sample aspiration height (in mm) from the bottom of the urine samples to aspirate from. Any well marked `X` in the csv, if uploaded will use this height. If the csv is not uploaded, all urine samples will use this height.
* `Sample Aspiration Height (mm)`: Specify the dispense height from the bottom of the 96 well plate to dispense sample. 
* `P300 Multi-Channel Mount`: Specify which mount (left or right) to host the P300 single channel pipette.


---

### Labware
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Opentrons 300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* NEST 100ul 96 well plate

### Pipettes
* [P300 Single Channel Pipette](link to pipette on shop.opentrons.com)

### Reagents
* Dilution buffer
* Enzyme Hydrolysis solution
* Urine Samples
* Trichloroacetic acid solution

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1dfebe/Screen+Shot+2021-11-08+at+5.20.33+PM.png)

---

### Protocol Steps
1. Use single channel to add 60ul of Enzyme Hydrolysis Solution from 15 ml conical tube to each well containing sample.
2. Use single channel to transfer 50ul of urine sample from sample tube to designated well in 96 well block. Repeat for all samples using a new tip each time.
3. Delay for 30 minutes after addition of Enzyme Hydrolysis solution to last well.
4. Use single channel to add 20ul of Trichloroacetic acid solution from 15 mL conical tube to each well containing sample.
5. Pause run until "Resume" is initiated (to manually shake the block).
6. Use single channel to add 150 of Dilution Buffer to each well containing sample.

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
1dfebe
