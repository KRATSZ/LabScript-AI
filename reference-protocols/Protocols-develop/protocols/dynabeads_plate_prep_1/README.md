# Dynabeads for IP Reagent-In-Plate Plate Prep 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Protein Purification
	* Thermo Fisher Dynabeads™ Protein A

## Description
This protocol (Plate Prep 1) performs pipetting to transfer reagents (Dynabeads and antibody dilution) from 15 mL conical tubes to a 96 well deepwell plate (the reagent plate) on the OT2. This reagent plate is used for Dynabeads for IP Reagent-In-Plate protocol Part 1. The user can determine the number of samples to be processed.

### Labware
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [4-in-1 Tube Rack Set](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [NEST 15 mL Centrifuge Tube](https://shop.opentrons.com/nest-15-ml-centrifuge-tube/)
* [Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

### Pipettes
P300 Single-Channel GEN2 (https://opentrons.com/pipettes/)

### Reagents
* [Thermo Fisher Dynabeads™ Protein A](https://www.thermofisher.com/order/catalog/product/10002D)
* [Thermo Fisher Dynabeads™ Protein G](https://www.thermofisher.com/order/catalog/product/10004D)
* [GAPDH Polyclonal antibody](https://www.ptglab.com/products/GAPDH-Antibody-10494-1-AP.htm) or comparable products from other vendors

### Deck Setup
* Slot 4 – 96 well deepwell plate (reagent plate)
* Slot 5 - Tube rack/reagent in 15 mL conical tube (reagent stock)

* Green – beads
* Blue – antibody

![deck setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/dynabeads_plate_prep_1/deck.png)

### Reagent Setup
* Beads: 50 uL per sample
* Antibody: diluted in phosphate-buffered saline with 0.1% Tween 20 (PBS-T), 50uL per sample

![reagent table](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/dynabeads_plate_prep_1/Screen+Shot+2022-04-14+at+5.35.27+PM.png)

### Protocol Steps
1. Bead slurry (reagent stock in 15 mL tubes, slot 5) is transferred to
the reagent plate (96 well deepwell plate A1-H1, slot 4) by the single
channel pipette.
2. Antibody solutions (reagent stock in 15 mL tubes, slot 5) is
transferred to the reagent plate (96 well deepwell plate A2-H2, slot 4)
by the single channel pipette.

![well distributions](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/dynabeads_plate_prep_1/Screen+Shot+2022-04-14+at+5.35.37+PM.png)

### Process
1. Input your protocol parameters (the number of samples to be processed).
2. Download your protocol.
3. Upload your protocol into the OT App.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App. For
calibration tips, check out our support articles.
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol
Development Team by filling out the [Troubleshooting
Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
dynabeads_plate_prep_1
