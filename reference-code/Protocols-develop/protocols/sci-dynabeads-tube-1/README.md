# Dynabeads for IP Reagent-In-Tube Part 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Protein Purification
	* Thermo Fisher Dynabeads™ Protein A/G

## Description
This protocol (Part 1) performs pipetting and mixing of reagents and samples on the OT2 as the first part of automated immunoprecipitation using Thermo Fisher Dynabeads Protein A or Protein G.

The user can determine the number of samples to be processed.

The samples (e.g. cell lysates), Dynabeads and the antibody specific for the protein of interest will be transferred to and mixed in a 96-well deepwell working plate on the OT2. The first part of the protocol completes at this point allowing the user to move the working plate to an agitation device, an antibody/target protein incubation period determined by the user. After incubation, the process proceeds with the second part of the protocol on the OT2. Dynabeads/antibody/target protein complex will be washed, eluted, and heated to denature. The final product is ready for SDS-PAGE.  

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [NEST 1-Well Reservoirs, 195 mL](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/)
* [4-in-1 Tube Rack Set](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [NEST 15 mL Centrifuge Tube](https://shop.opentrons.com/nest-15-ml-centrifuge-tube/)
* [Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

### Pipettes
* [P300 Single-Channel GEN2](https://opentrons.com/pipettes/)
* [P300 8-Channel GEN2](https://opentrons.com/pipettes/)

### Reagents
* [Thermo Fisher Dynabeads™ Protein A](https://www.thermofisher.com/order/catalog/product/10002D)
* [Thermo Fisher Dynabeads™ Protein G](https://www.thermofisher.com/order/catalog/product/10004D)
* [GAPDH Polyclonal antibody](https://www.ptglab.com/products/GAPDH-Antibody-10494-1-AP.htm) or comparable products from other vendors

### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-dynabeads-tube-1/deck_updated.png)  
* Beads: 50 uL per sample
* Antibody: diluted in phosphate-buffered saline with 0.1% Tween 20 (PBS-T), 50 uL per sample  


### Reagent Setup
* Beads: 50 uL per sample  
* Antibody: diluted in phosphate-buffered saline with 0.1% Tween 20 (PBS-T), 50 uL per sample  
![volumes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-dynabeads-tube-1/vols.png)  

### Protocol Steps
1. Bead slurry (in a 15 mL tube, slot 4) is transferred to the working plate (slot 1) by the single-channel pipet, and supernatant removed with magnetic module on.
2. Antibody solution (in a 15 mL tube, slot 4) is transferred to the working plate (slot 1) by the single-channel pipet.
3. Samples (in 96 deepwell plate, slot 5) are transferred to the working plate (slot 1) by the 8-channel pipet) and mixed by pipetting up and down (10 times)
4. The working plate is sealed and moved to a shaker.

### Process
1. Input your protocol parameters (the number of samples to be processed).
2. Download your protocol.
3. Upload your protocol into the OT App.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App.
6. For calibration tips, check out our support articles.
7. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
sci-dynabeads-tube-1
