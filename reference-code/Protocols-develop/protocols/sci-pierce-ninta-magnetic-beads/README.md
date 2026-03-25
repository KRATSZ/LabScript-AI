# Pierce NiNTA Magnetic Beads Part 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Protein Purification
     * Thermo Fisher Pierce Ni-NTA Magnetic Agarose Beads

## Description

This protocol (Part 1) performs pipetting and mixing of reagents and samples on the OT2 as the first part of automated process of His-tagged protein purification using Pierce Ni-NTA Magnetic Agarose Beads.

The user can determine the number of samples to be processed, and if desired, a second elution step can be performed to increase recovery.

The sample containing His-tagged protein (target protein) and Ni-NTA magnetic beads (beads) will be transferred to and mixed in a 96-well deepwell working plate on the OT2. The first part of the protocol completes at this point allowing the user to move the working plate to an agitation device, a beads/target protein incubation period determined by the user. After incubation, the process proceeds with the second part of the protocol on the OT2. Beads/target protein complex will be washed, and target protein eluted for further analysis.

Links:
* [Opentrons Protocol part-1: Pierce NiNTA Magnetic Beads](https://protocols.opentrons.com/protocol/sci-pierce-ninta-magnetic-beads)

* [Opentrons Protocol part-2: Pierce NiNTA Magnetic Beads: part-2](https://protocols.opentrons.com/protocol/sci-pierce-ninta-magnetic-beads-part-2)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Thermo Fisher Pierce Ni-NTA Magnetic Agarose Beads](https://www.thermofisher.com/order/catalog/product/78606)
* Equilibration buffer (Equilibration buffer (50 mM sodium phosphate, 300 mM sodium chloride, 20 mM imidazole, pH 7.4)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)

* [Magnetic Module GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [NEST 1-Well Reservoirs, 195 mL](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [4-in-1 Tube Rack Set](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [NEST 15 mL Centrifuge Tube](https://shop.opentrons.com/nest-15-ml-centrifuge-tube/)

* [Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

* [P300 Single-Channel GEN2](https://opentrons.com/pipettes/)
* [P300 8-Channel GEN2](https://opentrons.com/pipettes/)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup

* Slot 1 - Magnetic module/96 deepwell plate (working plate)
* Slot 4 – Equilibration buffer in 12 well reservoir (blue)
* Slot 5 - Tube rack/beads in 15 mL conical tube (Green)
* Slot 7 - Samples in 96 well deepwell plate (red)
* Slot 8 – Liquid waste
* Slot 9 – Tiprack1
* Slot 10 – Tiprack2

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-pierce-ninta-magnetic-beads/screenshot+deck-31.png)

* Beads: 50 uL per sample
* Equilibration buffer: 450 uL and 500 uL per sample

![table](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-pierce-ninta-magnetic-beads/screenshot+table-31.png)


## Protocol Steps

1. Bead slurry (in a 15 mL tube, slot 5) is transferred to the working plate (slot 1) by the single-channel pipet
2. Equilibration buffer (slot 4) is transferred to the working plate (slot 1) by the 8-channel pipet, and then supernatant removed with magnetic module on.
3. Again, equilibration buffer (slot 4) is transferred to the working plate (slot 1) by the 8-channel pipet, and supernatant removed with magnetic module on.
4. Samples (in 96 deepwell plate, slot 7) are transferred to the working plate (slot 1) by the 8-channel pipet and mixed by pipetting up and down (10 times)
5. The working plate is sealed and moved to a shaker.


## Process
1. Input your protocol parameters (the number of samples to be processed).
2. Download your protocol.
3. Upload your protocol into the OT App.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our support articles.
6. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
sci-pierce-ninta-magnetic-beads
