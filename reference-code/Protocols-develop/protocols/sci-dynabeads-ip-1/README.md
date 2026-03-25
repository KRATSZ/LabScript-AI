# Dynabeads for IP Reagent-In-Plate Part 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Protein Purification
	* ThermoFisher Dynabeads Protein A/G

## Description
This protocol (Part 1) performs pipetting and mixing of reagents and samples on the OT2 as the first part of automated immunoprecipitation using Thermo Fisher Dynabeads Protein A or Protein G.

The user can determine the number of samples to be processed.

The samples (e.g. cell lysates), Dynabeads and the antibody specific for the protein of interest will be transferred to and mixed in a 96-well deepwell working plate on the OT2. The first part of the protocol completes at this point allowing the user to move the working plate to an agitation device, an antibody/target protein incubation period determined by the user. After incubation, the process proceeds with the second part of the protocol on the OT2. Dynabeads/antibody/target protein complex will be washed, eluted, and heated to denature. The final product is ready for SDS-PAGE.  

---

### Modules
[Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)


### Labware
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [NEST 1-Well Reservoirs, 195 mL](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/)
* [Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

### Pipettes
[P300 8-Channel GEN2](https://shop.opentrons.com/pipettes/)


### Reagents
* [Thermo Fisher Dynabeads™ Protein A](https://www.thermofisher.com/order/catalog/product/10002D), **or**
* [Thermo Fisher Dynabeads™ Protein G](https://www.thermofisher.com/order/catalog/product/10004D)
* [GAPDH Polyclonal antibody](https://www.ptglab.com/products/GAPDH-Antibody-10494-1-AP.htm) or comparable products from other vendors

---

### Deck Setup
Slot 1 - Magnetic module/96 deepwell plate (working plate)</br>
Slot 3 - Temperature module</br>
Slot 4 – Reagent in 96 well deepwell plate</br>
  a.	Green – beads</br>
  b.	Blue – antibody</br>
Slot 5 - Samples in 96 well deepwell plate (red)</br>
Slot 7 - Tiprack1</br>
Slot 8 - Tiprack2 </br>
Slot 9 – Liquid waste</br>
</br>
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-dynabeads-ip/sci-dynabeads-deck.png)

### Reagent Setup
**Beads**: 50 uL per sample</br>
**Antibody**: diluted in phosphate-buffered saline with 0.1% Tween 20 (PBS-T), 50 uL per sample


---

### Protocol Steps
1. Bead slurry (in reagent plate, slot 4) is transferred to the working plate (slot 1) by the 8-channel pipet, and supernatant removed with magnetic module on.
2. Antibody solution (in reagent plate, slot 4) is transferred to the working plate (slot 1) by the 8-channel pipet.
3. Samples (in 96 deepwell plate, slot 5) are transferred to the working plate (slot 1) by the 8-channel pipet and mixed by pipetting up and down (10 times)
4. The working plate is sealed and moved to a shaker.


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
protocol-hex-code
