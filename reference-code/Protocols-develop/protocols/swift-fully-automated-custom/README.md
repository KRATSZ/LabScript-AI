# Swift 2S Turbo DNA Library Kit Protocol: Fully Automated (Custom)

### Author
[Opentrons (verified)](https://opentrons.com/)

### Partner
[Swift Biosciences](https://swiftbiosci.com/)



## Categories
* NGS Library Prep
	* Swift 2S Turbo


## Description
![Swift Biosciences](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/swift-2s-protocol/swift_logo.jpg)

This protocol is a custom modification to the [Swift 2S Turbo DNA Library Kit Protocol: Fully Automated](https://protocols.opentrons.com/protocol/swift-fully-automated) already found in the Opentrons Protocol Library. This version of the protocol features lowers aspiration flow rates to avoid bead pick-up, longer incubation times, and less volume of supernatant removed. This version also features both generations of the magnetic module. If running 24 samples with this protocol, the protocol will stop when it runs out of tips, prompting the user to replace tip racks.

With this protocol, your [OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2) can **fully automate** the entire [Swift 2S Turbo DNA Library Kit](https://swiftbiosci.com/swift-2s-turbo-dna-library-kits/). Simply press start and your OT-2 can automate this entire workflow without any hands-on requirement - from enzymatic prep to sequence ready libraries! Up to 16 libraries can be prepared in under 3 hours.


For more information about the Swift 2S Turbo Kit and the [Swift 2S Turbo Unique Dual Indexing Primer Kit](https://shop.opentrons.com/products/swift-2s-turbo-unique-dual-indexing-primer-kit-96-rxns?_pos=1&_sid=f1fb599e7&_ss=r) on the OT-2, please see our Application Note here: [Rapid high quality next generation sequencing library preparation with Swift 2S Turbo DNA Library Kits on the Opentrons OT-2](https://opentrons-landing-img.s3.amazonaws.com/bundles/swift_automated_ngs_application_note.pdf)</br>
</br>


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase consumables, labware, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)


**Attention**: You can now purchase all of the consumables needed to run this protocol by [clicking here](https://shop.opentrons.com/products/ngs-library-prep-workstation-consumables-refill).

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Swift 2S Turbo DNA Library Kit](https://swiftbiosci.com/swift-2s-turbo-dna-library-kits/)
* [Swift 2S Turbo Unique Dual Indexing Primer Kit](https://shop.opentrons.com/products/swift-2s-turbo-unique-dual-indexing-primer-kit-96-rxns?_pos=1&_sid=f1fb599e7&_ss=r)
* [Omega Mag-Bind TotalPure NGS Kit](https://shop.opentrons.com/collections/verified-reagents/products/mag-bind-total-pure-ngs)
* [Opentrons Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)
* [Opentrons Temperature Module with Aluminum Block Set](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) or Opentrons P50 Single-Channel Pipette*
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [NEST 2mL Tubes](https://shop.opentrons.com/collections/tubes/products/nest-2-0-ml-sample-vial)
* Samples, resuspended in Low EDTA TE, bringing the total volume to 19.5µL



\*Opentrons now sells the P20 Single-Channel Pipette in place of the P50 Single-Channel Pipette. If you have the P50 Single-Channel Pipette, you can use it for this protocol.


Full setup for the entire protocol:

![Full Deck Layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/swift-2s-protocol/swift-fa-layout.png)

![Layout of Reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/swift-2s-protocol/swift-fa-labware.jpeg)




---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)


Slot 1: [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) on [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)


Slot 2: [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml) with Reagents
* A2: Magnetic Beads; recommended volume: 3-4mL, 4-5mL if running 24 samples.
* A3: 80% Ethanol Solution, Freshly Prepared; recommended volume: 9-10mL, max allowable reservoir well volume if running 24 samples (watch for overflowing if the multi-channel pipette dunks).
* A4: 80% Ethanol Solution, Freshly Prepared (if running 16 samples); recommended volume: 9-10mL, max allowable reservoir well volume if running 24 samples (watch for overflowing if the multi-channel pipette dunks).
* A6: Low EDTA TE Buffer; recommended volume: ~3mL


Slot 3: [Opentrons Temperature Module with 24-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) and [NEST 2mL Tubes](https://shop.opentrons.com/collections/tubes/products/nest-2-0-ml-sample-vial) with master mixes (for more information on master mixes, [click here](https://opentrons-protocol-library-website.s3.amazonaws.com/Technical+Notes/swift-fully-automated-custom/Swift+2s+Turbo+Fully+Automated+MasterMix+Volumes+(1).xlsx)) and indices (if automating index addition)
* A1: Enzymatic Prep Master Mix
* A2: Ligation Master Mix
* A3: PCR Master Mix
* B1: Indexing Reagent 1 (in original container); loaded sequentially (Reagent 2 - B2; Reagent 3 - B3...)


Slot 4: [Opentrons Tips for Single-Channel Pipette](https://shop.opentrons.com/collections/opentrons-tips)


Slot 5: [Opentrons Tips for P300 8-Channel Pipette](https://shop.opentrons.com/collections/opentrons-tips)


Slot 6: [Opentrons Tips for P300 8-Channel Pipette](https://shop.opentrons.com/collections/opentrons-tips)


Slot 9: [Opentrons Tips for P300 8-Channel Pipette](https://shop.opentrons.com/collections/opentrons-tips)



Slot 7/8/10/11: [Opentrons Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module) with samples in a [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* 8 Samples: Column 1
* 16 Samples: Columns 1 & 2



__Using the customizations fields, below set up your protocol.__
* **Number of Samples**: Specify the number of samples (8, 16, 24) you'd like to run.
* **Pipette and Tip Type**: Select which pipette (P50 Single-Channel or P20 Single-Channel) and corresponding tips to be used for this protocol. **The pipette should be attached to the left mount.**
* **P300 8-Channel Pipette Tip Type**: Select which tips (Filter/Non-Filter) for P300 8-Channel Pipette
* **Automate Indexing**: Specify whether the indices should be added to the samples with the OT-2, or manually.
* **Number of PCR Cycles**: See suggested cycles [here](https://opentrons-protocol-library-website.s3.amazonaws.com/Technical+Notes/swift-fully-automated-custom/Swift+Fully+Automated+-+PCR+Cycles+Recommendation.xlsx). See Swift 2S Turbo manual for more detailed information.
* **Fragmentation Time**: Fragmentation time varies depending on *1)* Lot number of the kit and *2)* whether the desired insert size is 200bp or 350bp. Please refer to the manual and Lot number on your kit for more information.



**Note**: The final 20µL elution will be transferred to Column 3 if running 8 samples, Columns 5 & 6 if running 16 samples, and Columns 5, 6, and 7 if running 24 samples of the PCR plate on the Thermocycler

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
swift-fully-automated-custom
