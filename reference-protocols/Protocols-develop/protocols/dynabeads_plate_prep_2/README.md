# Dynabeads for IP Reagent-In-Plate Plate Prep 2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Protein Purification
	* Thermo Fisher Dynabeads™ Protein A

## Description
This protocol (Plate Prep 2) performs pipetting to transfer elution buffer from 15 mL conical tubes to a 96 well deepwell plate (the reagent plate) on the OT2. This reagent plate is used for Dynabeads for IP Reagent-In-Plate protocol Part 2. The user can determine the number of samples to be processed.

### Labware
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [4-in-1 Tube Rack Set](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [NEST 15 mL Centrifuge Tube](https://shop.opentrons.com/nest-15-ml-centrifuge-tube/)
* [Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

### Pipettes
* [P300 Single-Channel GEN2](https://opentrons.com/pipettes/)

### Reagents
* [2x Laemmli Sample Buffer](https://www.bio-rad.com/en-us/sku/1610737-2x-laemmli-sample-buffer?ID=1610737) with reducing agent β-mercaptoethanol (BME)

### Deck Setup
* Slot 4 – 96 well deepwell plate (reagent plate)
* Slot 5 - Tube rack/reagent in 15 mL conical tube (reagent stock)

* Purple – elution buffer

![deck layout](https://opentrons-protocol-library-website.s3.us-east-1.amazonaws.com/custom-README-images/dynabeads_plate_prep_2/1.png)

### Reagent Setup
* Elution buffer: 30 uL 2x Laemmli Sample Buffer with 2.5% BME per sample

![reagent setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/dynabeads_plate_prep_2/2.png)

### Protocol Steps
1. Elution buffer (reagent stock in 15 mL tubes, slot 5) is transferred to the reagent plate (96 well deepwell plate A12-H12, slot 4) by the single channel pipet.

![well distributions](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/dynabeads_plate_prep_2/3.png)

### Process
1. Input your protocol parameters (the number of samples to be processed).
2. Download your protocol.
3. Upload your protocol into the OT App.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our support articles.
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
dynabeads_plate_prep_2
