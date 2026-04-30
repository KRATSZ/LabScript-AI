# PCR Plate Prep with 384 Well Plate

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Partner Name](partner website link)



## Categories
* PCR
	* PCR Prep

## Description
This protocol preps a 384 well sample plate with mastermix. Up to four plates can be loaded onto the deck with a no template control and human sample control in wells A1 and B1, respectively. Sample plates are transferred to the 384 well plate skipping wells down a column, as well as skipping columns (e.g. plate 1 to A1, C1, E1....H1, A3, C3, E3...etc). A positive control is added to the last well in the 384 well plate.

The protocol is broken down into 3 main parts:
* Mastermix distributed to 384 well plate.
* Sample added to 384 well plate.  
* Positive control added to plate.

Note: The protocol will prompt the user to put the specified amount of volume for all 3 mastermix reagents in the specified number of tubes at the beginning of the protocol.

Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples (1-96) that the sample block, elution buffer block, ethanol block, NPW3 block, and NPW4 block will be filled.
* `P20 Single Channel Mount (GEN2)`: Specify which mount the P20 Single Channel pipette will be mounted.
* `Percent overage`: Specify the overage percent to which mastermix will be made and distributed to the 384 well plate.
* `Mix repetitions`: Specify the number of mix repetitions for making mastermix, as well as after distributing sample to the mastermix.
---

### Labware
* Kingfisher 96 Well Plate
* 384 Well Plate
* [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 4-in-1 tube rack with 1.5mL tubes](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)

### Pipettes
* [P20 GEN2 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P300 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)


---

### Deck Setup

* Deck Layout with samples and controls loaded onto 96 well plates.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/13ea1e/pt2/Screen+Shot+2021-06-17+at+3.41.05+PM.png)

### Reagent Setup
* Tube rack: Slot 5. Positive control D6.

* Note on tube rack: please refer to the Opentrons app at the beginning of the protocol to determine how many mastermix tubes are needed. The by hand calculation, for reference, is 7ul X (number of samples) X (overage_percent)/1000. A new mastermix tube is "made" on the deck every 1000ul, (i.e. maximum volume per mastermix tube is 1000ul). If the volume exceeds 1000ul, split the volumes between the tubes equally, as the OT-2 will access mastermix tubes sequentially when distributing (e.g. A1 to plate, A2 to plate, A3 to plate, A1 to plate, etc.). Examples: (a) 900ul of mastermix just in tube A1. (b) 1100ul of mastermix is split into 550ul between tubes A1 and A2. This is all demonstrated in the app at the beginning of the protocol.  

![tube rack](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/13ea1e/pt2/Screen+Shot+2021-06-17+at+3.41.32+PM.png)

---

### Protocol Steps

1. Mastermix is distributed to the 384 well plate depending on which wells will eventually have sample.
2. Sample is added to these wells and mixed.
3. Positive control is added to the last well in the plate.

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
13ea1e-part2
