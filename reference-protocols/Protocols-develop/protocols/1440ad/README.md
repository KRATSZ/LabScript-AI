# Extraction with Mag-Bind TotalPure NGS kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* RNA Extraction

## Description
This protocol extracts RNA using two temperature modules and a magnetic module. The protocol can be considered in 5 main parts:

* Reagent added to sample
* Sample moved to magnetic plate
* Mag Beads added to sample
* Two ethanol washes with magnet engagement
* Water added to samples
* Samples added to final tube rack


Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples for this run.
* `Number of Mag Bead Tubes`: Specify the number of tubes to store the magnetic beads in column 6 of the room temperature reagent rack. Note: mag bead volume should be split equally between the number of tubes specified. 
* `Mag Bead Resuspend Volume`: Specify the volume to mix the beads for resuspension before they are added to a sample.
* `Mag Bead Resuspend Mix Repetions`: Specify the number of repetitions to mix `Mag Bead Resuspend Volume` before the mag beads are added to the sample.
* `RR1-TR10 Volume`: Specify the volume of each respective reagent to put into each sample.
* `P20 Single Channel Mount`: Specify which mount (left or right) to place the P20 single channel pipette.
* `P300 Single Channel Mount`: Specify which mount (left or right) to place the P20 single channel pipette.


---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/collections/lab-plates/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Opentrons 300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Pipettes
* [P20 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P300 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)


### Reagents
[Omega Bio-tek Mag-Bind® TotalPure NGS](https://www.omegabiotek.com/product/mag-bind-totalpure-ngs/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1440ad/Screen+Shot+2021-07-01+at+12.32.29+PM.png)

### Reagent Setup

* Tube Rack Slot 2:

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1440ad/Screen+Shot+2021-07-01+at+12.18.47+PM.png)

* Samples Slot 3:

![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1440ad/Screen+Shot+2021-07-01+at+12.18.57+PM.png)

* Reservoir Slot 5:

![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1440ad/Screen+Shot+2021-07-01+at+12.18.27+PM.png)

* Cold Reagents on temperature module Slot 6:

![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1440ad/Screen+Shot+2021-07-01+at+12.18.33+PM.png)



---

### Protocol Steps
1. Cold reagents added to sample r1-r3
2. Room temperature non viscous reagents are added to sample tr1-tr6
3. Room temperature viscous reagents are added to sample tr7-tr9
4. Mix Every 30 minutes for two hours incubation
5. Add final Viscous reagent tr10 and mix
6. Transfer samples to mag plate
7. Add mag beads
8. Apply magnet
9. Remove supernatant
10. Two ethanol washes
11. Add water
12. Add to final tube rack


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
1440ad
