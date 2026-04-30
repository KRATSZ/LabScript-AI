# Swift 2S Turbo DNA Library Kit Protocol: Part 2/3 - Ligation Clean-Up & PCR Prep

### Author
[Opentrons (verified)](https://opentrons.com/)

### Partner
[Swift Biosciences](https://swiftbiosci.com/)



## Categories
* Featured
	* NGS Library Prep: Swift 2S Turbo


## Description
![Swift Biosciences](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/swift-2s-protocol/swift_logo.jpg)

Part 2 of 3: Ligation Clean-Up & PCR Prep


With this protocol, your [OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2) can perform the [Swift 2S Turbo DNA Library Kit](https://swiftbiosci.com/swift-2s-turbo-dna-library-kits/). For more information about the Swift 2S Turbo Kit and the [Swift 2S Turbo Unique Dual Indexing Primer Kit](https://shop.opentrons.com/products/swift-2s-turbo-unique-dual-indexing-primer-kit-96-rxns?_pos=1&_sid=f1fb599e7&_ss=r) on the OT-2, please see our Application Note here: [Rapid high quality next generation sequencing library preparation with Swift 2S Turbo DNA Library Kits on the Opentrons OT-2](https://opentrons-landing-img.s3.amazonaws.com/bundles/swift_automated_ngs_application_note.pdf)


In this part of the protocol, your OT-2 will complete the ligation process that was begun in [Part 1](http://develop.protocols.opentrons.com/protocol/swift-2s-turbo-pt1) and complete the indexing portion up to the thermocycling step (step 18) as outlined in the [Swift 2S Turbo Kit Guide](https://swiftbiosci.com/wp-content/uploads/2019/11/PRT-001-2S-Turbo-DNA-Library-Kit-Rev-1.pdf).


At the completion of this step, you will add your samples to the thermocycler. Once the thermocycler step is complete, continue with [Part 3 of the protocol](https://protocols.opentrons.com/protocol/swift-2s-turbo-pt3).


Links:
* [Part 1: Enzymatic Prep & Ligation](https://protocols.opentrons.com/protocol/swift-2s-turbo-pt1)
* [Part 2: Ligation Clean-Up & PCR Prep](https://protocols.opentrons.com/protocol/swift-2s-turbo-pt2)
* [Part 3: Final Clean-Up](https://protocols.opentrons.com/protocol/swift-2s-turbo-pt3)





---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)


**Attention**: You can now purchase all of the consumables needed to run this protocol by [clicking here](https://shop.opentrons.com/products/ngs-library-prep-workstation-consumables-refill).

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Swift 2S Turbo DNA Library Kit](https://swiftbiosci.com/swift-2s-turbo-dna-library-kits/)
[Swift 2S Turbo Unique Dual Indexing Primer Kit](https://shop.opentrons.com/products/swift-2s-turbo-unique-dual-indexing-primer-kit-96-rxns?_pos=1&_sid=f1fb599e7&_ss=r)
* [Omega Mag-Bind TotalPure NGS Kit](https://shop.opentrons.com/collections/verified-reagents/products/mag-bind-total-pure-ngs)
* [Opentrons Temperature Module with Aluminum Block Set](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) or Opentrons P50 Single-Channel Pipette
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [NEST 2mL Tubes](https://shop.opentrons.com/collections/tubes/products/nest-2-0-ml-sample-vial)
* Samples, user collected from [Part 1](https://protocols.opentrons.com/protocol/swift-2s-turbo-pt1)
* PCR Strip(s), *optional*


Full setup for the entire protocol:

![Full Deck Layout](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/swift-2s-protocol/deck_layout_names.png)

![Layout of Reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/swift-2s-protocol/labware_layout.jpeg)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

*Specific to Part 2 of 3*


Slot 1: [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) (or PCR Strips) on top of [96-Well Aluminum Block](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set) with samples the user has collected from [Part 1](https://protocols.opentrons.com/protocol/swift-2s-turbo-pt1)
* 8 Samples: Column 1
* 16 Samples: Columns 1 & 2
* 24 Samples: Columns 1, 2, & 3

Slot 2: [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* A1: Magnetic Beads
* A3: 80% Ethanol Solution, Freshly Prepared
* A4: 80% Ethanol Solution, Freshly Prepared
* A6: Low EDTA TE Buffer

Slot 3: [Opentrons Temperature Module with 24-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) and [NEST 2mL Tubes](https://shop.opentrons.com/collections/tubes/products/nest-2-0-ml-sample-vial) with master mixes (for more information on master mixes, [click here](https://opentrons-protocol-library-website.s3.amazonaws.com/Technical+Notes/swift-2s-turbo-pt1/Swift+2S+Turbo+Master+Mix+Volumes.xlsx)) and indices (if automating index addition)
* A1: (**used in Part 1**) Enzymatic Prep Master Mix
* A2: (**used in Part 1**) Ligation Master Mix
* A3: PCR Master Mix
* B1: Indexing Reagent 1 (in original container); loaded sequentially (Reagent 2 - B2; Reagent 3 - B3...)
*Note*: if the user is running 24 samples and chooses to automate indices addition, the robot will pause after addition of the first 16 indices to allow user to replace them with the final 8 indices.

Slot 4: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)

Slot 5: [Opentrons Tips for Single-Channel Pipette](https://shop.opentrons.com/collections/opentrons-tips)


Slot 6: [Opentrons Tips for P300 8-Channel Pipette](https://shop.opentrons.com/collections/opentrons-tips)


Slot 9: [Opentrons Tips for P300 8-Channel Pipette](https://shop.opentrons.com/collections/opentrons-tips)



**Using the customizations fields, below set up your protocol.**
* **Pipette and Tip Type**: Select which pipette (P50 Single-Channel or P20 Single-Channel) and corresponding tips to be used for this protocol. **The pipette should be attached to the left mount.**
* **P300 8-Channel Pipette Tip Type**: Select which tips (filter/non-filter) to be used for this protocol.
* **Number of Samples**: Specify the number of samples (8, 16, or 24) you'd like to run.
* **Magdeck Generation**: Specify whether using Generation 1 or Generation 2 magdeck.
* **Automate Indexing**: Specify whether the indices should be added to the samples with the OT-2, or manually.




### Robot
* [OT-2](https://opentrons.com/ot-2)

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
Swift-2S-Turbo-pt2
