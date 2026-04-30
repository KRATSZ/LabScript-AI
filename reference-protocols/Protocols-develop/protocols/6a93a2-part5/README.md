# Swift Rapid NGS Part 5 - Indexing and SPRI Clean

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Swift Biosciences](https://swiftbiosci.com/protocols/)



## Categories
* NGS Library Prep
	* Swift Rapid RNA Library Kit

## Description
This protocol is part five of a five-part series to perform Swift Biosciences Rapid NGS Library Prep kit. The protocol is split in such a way so as to allow for the option to run between the Rapid and Standard versions of the kit. Please find all linked parts of the protocol below:

Links:
* [Swift NGS Part 1 - Reverse Transcription and SPRI Cleanup](https://protocols.opentrons.com/protocol/6a93a2)
* [Swift Rapid NGS Part 2 - Adaptase](https://protocols.opentrons.com/protocol/6a93a2-part2)
* [Swift Rapid NGS Part 3 - Extension, SPRI, and Ligation](https://protocols.opentrons.com/protocol/6a93a2-part3)
* [Swift Rapid NGS Part 4 - SPRI Clean](https://protocols.opentrons.com/protocol/6a93a2-part4)

Part five of this protocol is divided into the following methods for 8, 16, or 24 samples:

* Indexing PCR
* SPRI Cleanup

Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples that will be processed.
* `PCR Mastermix Overage Percent`: Specify the percent overage of Reverse Transcription Mastermix to make and ultimately add to samples.
* `Bead Drying Time`: Specify the amount of time after both ethanol washes are completed and the plate is spun down to let the beads dry.
* `Opentrons 96 Tip Rack 20ul Tip Type`: Specify whether filter or non-filter 20ul tips will be employed.
* `Index Start Column`: Specify which column on the index plate to begin aspirating from.
* `Number of Thermocycler Cycles`: Specify the number of repetitions samples will undergo a (20 second, 98C), (30 second, 60C), and (30 second, 72C) profile in the thermocycler (based on purity)
* `P300 Multi GEN2 Mount`: Specify which mount (left or right) to load the P300 multi channel pipette.
* `P20 Single GEN2 Mount`: Specify which mount (left or right) to load the P20 single channel pipette.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Labware
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 200uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 24-Tube Aluminum Block](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)
* Thermofisher Armadillo 96 Wellplate 200ul


### Pipettes
* [P20 GEN2 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P300 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Reagents
* [Swift Rapid RNA Library Kit](https://swiftbiosci.com/wp-content/uploads/2020/04/PRT-024-Swift-Rapid-RNA-Library-Kit-Protocol-v3.0.pdf)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6a93a2/pt5/Screen+Shot+2021-05-05+at+4.22.01+PM.png)

### Reagent Setup
* Reservoir: Slot 2

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6a93a2/pt5/Screen+Shot+2021-05-05+at+4.22.43+PM.png)

---

### Protocol Steps
1. Index primers are added to sample wells.
2. PCR mastermix is added to each well.
3. Samples undergo thermocycle profile.
4. Magnetic beads are added to samples.
5. Samples are incubated at room temperature.
6. Protocol pauses - plate is removed from deck, sealed and spun down.
7. Plate is placed back on magnetic module.
8. Supernatant removed.
9. Two ethanol washes of samples with 30 second incubation periods before supernatant is removed.
10. Protocol pauses - plate is removed from deck, sealed and spun down.
11. Low EDTA TE is added to beads, incubate.  
12. Protocol pauses - plate is removed from deck, sealed and spun down.
13. Supernatant is moved to columns 9, 10, 11.



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
6a93a2-part5
