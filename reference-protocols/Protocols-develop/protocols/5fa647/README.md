# SuperScript™ III: qRT-PCR Prep with CSV File

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Invitrogen](https://www.thermofisher.com/order/catalog/product/11752250#/11752250)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs the [SuperScript™ III Real Time PCR Kit](https://www.thermofisher.com/order/catalog/product/11752250#/11752250) by Invitrogen. Enzyme and 2X RT Reaction mix are combined in a mix tube and distributed to the center 3 columns of a 96 well plate on the Opentrons Thermocycler module. The protocol is split into 5 main parts:

* 2X RT Reaction Mix and Enzyme Mix are combined in an empty tube, mixed, and then distributed to the PCR plate on the thermocycler.
* RNA sample is added to the PCR plate on the thermocycler. Solution is mixed.
* Temperature profile is run on thermocycler as per kit instruction.
* Protocol pauses and user is prompted to chill PCR plate on ice.
* RNase H and Water are added to sample.


Explanation of complex parameters below:
* `CSV`: Upload a CSV which specifies the amount of RNA to be transferred for each well.
The CSV should be formatted like so:

`Well` | `Transfer Volume (ul)`

The first row should contain headers (like above). All following rows should just include necessary information. </br>

Samples should be placed in the Opentrons Aluminum tube rack, as well as referenced in the CSV in order by column (e.g. A1, B1, C1, etc.) up to the number of samples for the run.

* `Number of Samples`: Specify number of samples (1-24) for this run.
* `P300 Single Mount`: Specify which mount the P300 is on (left or right).
* `P20 Single Mount`: Specify which mount the P20 is on (left or right).
---

### Modules
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)


### Labware
* [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)
* [Opentrons 96 Filter Tip Rack 200 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_200ul?category=tipRack)
* [Opentrons 24 well Aluminum tube rack](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)
* [NEST 100ul Full Skirted PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)

### Pipettes
* [P20 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P300 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

### Reagents
* [SuperScript™ III Real Time PCR Kit](https://www.thermofisher.com/order/catalog/product/11752250#/11752250)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5fa647/Screen+Shot+2021-04-20+at+9.34.00+AM.png)

### Reagent Setup
* Reagent Tubes, Slot 2
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5fa647/Screen+Shot+2021-04-20+at+10.08.56+AM.png)

---

### Protocol Steps
1. Mix 10ul (per sample) of 2x RT Rxn Mix + 2ul (per sample) of RT Enzyme Mix in a tube using a single channel pipette.
2. Pipette 12ul of the mix from step 1 into PCR Plate. (# of tubes = # samples per run). Use same tip.
3. Using a single channel pipette, pipette designated amount of RNA (per CSV) from the sample tube rack into the PCR Plate containing the mix from step 1, and pipette mix. Change tips between each sample.
4. Heat at 25C for 10 minutes
5. Heat at 50C for 30 minutes
6. Heat at 85C for 5 minutes, then chill on ice
7. Add 1ul of RNase H to each sample (new tip for each sample)
8. Heat at 37C for 20 minutes.
9. Add 60ul of water to each sample (new tip each sample)
10. Store on ice

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
5fa647
