# Pierce NiNTA Magnetic Beads Part 2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Protein Purification
     * Thermo Fisher Pierce Ni-NTA Magnetic Agarose Beads

## Description

This protocol (Part 2) performs washing and elution on the OT2 as the second part of automated process of His-tagged protein purification using Pierce Ni-NTA Magnetic Agarose Beads.

The user can determine the number of samples to be processed, and if desired, a second elution step can be performed to increase recovery.

The sample containing His-tagged protein (target protein) and Ni-NTA magnetic beads (beads) will be transferred to and mixed in a 96-well deepwell working plate on the OT2. The first part of the protocol completes at this point allowing the user to move the working plate to an agitation device, a beads/target protein incubation period determined by the user. After incubation, the process proceeds with the second part of the protocol on the OT2. Beads/target protein complex will be washed, and target protein eluted for further analysis.

Links:
* [Opentrons Protocol part-1: Pierce NiNTA Magnetic Beads](https://protocols.opentrons.com/protocol/sci-pierce-ninta-magnetic-beads)

* [Opentrons Protocol part-2: Pierce NiNTA Magnetic Beads: part-2](https://protocols.opentrons.com/protocol/sci-pierce-ninta-magnetic-beads-part-2)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* Wash buffer (50 mM sodium phosphate, 300 mM sodium chloride, 40 mM imidazole, pH 7.4)
* Elution buffer (50 mM sodium phosphate, 300 mM sodium chloride, 300 mM imidazole, pH 7.4)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)

* [Magnetic Module GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [NEST 1-Well Reservoirs, 195 mL](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)

* [Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

* [P300 8-Channel GEN2](https://opentrons.com/pipettes/)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup

* Slot 1 - Magnetic module/sample + beads (red) in 96 well deepwell plate (working plate)
* Slot 2 – Elution buffer in 12 well reservoir (orange)
* Slot 3 - 96 well deepwell plate (final plate)
* Slot 4 – Wash buffer in 12 well reservoir (purple)
* Slot 5 – Tiprack1 (Note: this tiprack is assigned for use in wash steps. The tips are returned to the tiprack and reused and will not be discarded.)
* Slot 6 – Tiprack2 (Note: this tiprack is assigned for use in elution steps. The tips are returned to the tiprack and reused and will not be discarded.)

![table2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-pierce-ninta-magnetic-beads/screenshot+table2-32.png)

* Slot 7 – Tiprack3
* Slot 8 – Liquid waste

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-pierce-ninta-magnetic-beads/screenshot+deck-32.png)

Wash buffer: 500 uL per sample per wash, i.e. 1,000 uL for 2 washes per sample (Note: Each well should contain at least 8,000 uL wash buffer, sufficient for 2 washing runs of 8 samples)
Elution buffer: 250 uL per sample per wash or 500 uL for 2 elutions per sample (Note: each well should contain at least 2,000 uL for 1 elution (or 4,000 uL for 2 elutions) of 8 samples)

![table1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-pierce-ninta-magnetic-beads/screenshot+table1-32.png)

## Protocol Steps

1. The mixture of sample and beads after incubation (working plate) is moved back to the magnetic module (slot 1), and Part 2 starts.
2. Supernatant in the working plate is removed by the 8-channel pipet with magnetic module on.
2. Wash buffer is transferred (slot 4) to the working plate (slot 1), and precipitated beads resuspended (magnetic module off), re-precipitated and supernatant removed (magnetic module on).
3. Step 2 repeats 1 more time. All wash steps are handled by the 8-channel pipet, and the tips reused.
4. Elution buffer (slot 2) is transferred to the working plate (slot 1) by the 8-channel pipet, and precipitated beads resuspended.
5. The protocol pauses. The working plate is sealed, agitated on a shaker for 10 minutes at room temperature and then moved back to magnetic module (slot 1).
6. Eluates are transferred to the final plate (slot 2) by the 8-channel pipet (magnetic module on).
7. Step 4-6 repeats 1 more time, if desired.

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
sci-pierce-ninta-magnetic-beads-part-2
