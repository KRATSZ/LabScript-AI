# Dynabeads for IP Reagent-In-Plate Part 2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Protein Purification
	* ThermoFisher Dynabeads Protein A/G

## Description
This protocol (Part 2) performs washing and elution on the OT2 as the second part of automated immunoprecipitation using Thermo Fisher Dynabeads Protein A or Protein G.

The user can determine the number of samples to be processed.

The samples (e.g. cell lysates), Dynabeads and the antibody specific for the protein of interest will be transferred to and mixed in a 96-well deepwell working plate on the OT2. The first part of the protocol completes at this point allowing the user to move the working plate to an agitation device, an antibody/target protein incubation period determined by the user. After incubation, the process proceeds with the second part of the protocol on the OT2. Dynabeads/antibody/target protein complex will be washed, eluted and heated to denature. The final product is ready for SDS-PAGE.  


---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)


### Labware
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [NEST 1-Well Reservoirs, 195 mL](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* [Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

### Pipettes
[P300 8-Channel GEN2](https://shop.opentrons.com/pipettes/)


### Reagents
* [2x Laemmli Sample Buffer](https://www.bio-rad.com/en-us/sku/1610737-2x-laemmli-sample-buffer?ID=1610737) with reducing agent β-mercaptoethanol (BME)
* [Pierce™ 20X PBS Tween™ 20 Buffer PBS-T](https://www.thermofisher.com/order/catalog/product/28352)


---

### Deck Setup
Slot 1 - Magnetic module/sample + beads + antibody (red) in 96 deepwell plate (working plate)</br>
Slot 2 – Wash buffer in 12 well reservoir (orange)</br>
Slot 3 - Temperature module/96 well PCR plate (final plate)</br>
Slot 4 – Reagent in 96 well deepwell plate/elution buffer (purple)</br>
Slot 5 – Tiprack3 (Note: this tiprack is assigned for use in 3 wash steps. The tips are returned to the tiprack and reused and will not be discarded.)</br>
Slot 6 – Tiprack4</br>
Slot 7 - Tiprack1</br>
Slot 8 - Tiprack2</br>
Slot 9 – Liquid waste</br>
</br>
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-dynabeads-ip/sci-dynabeads-deck2.png)

### Reagent Setup
**Elution buffer**: 30 uL 2x Laemmli Sample Buffer with 2.5% BME per sample</br>
**Wash buffer (PBS-T)**: 200 uL per sample per wash, i.e. 600 uL for 3 washes per sample (Note: Each well of the 12 well reservoir should contain enough wash buffer for 3 washing runs of 8 samples (1 column in working plate). It is recommended to fill each well with 5,000 uL wash buffer)



---

### Protocol Steps
1. The mixture of sample, antibody and beads after incubation (working plate) is moved back to the magnetic module (slot 1), and Part 2 starts.
2. Supernatant in the working plate is removed by the 8-channel pipet with magnetic module on.
2. Wash buffer is transferred (slot 2) to the working plate (slot 1), and precipitated beads resuspended (magnetic module off), re-precipitated and supernatant removed (magnetic module on).
3. Step 2 repeats 2 more times. All wash steps are handled by the 8-channel pipet, and the tips reused.
4. Elution buffer (in reagent plate, slot 4) is transferred to the working plate (slot 1) by the 8-channel pipet.
5. Beads and elution buffer is mixed and transferred by the 8-channel pipet to the final plate (slot 3).
6. The final plate is sealed, and temperature module activated and set to heat the final plate for 10 minutes at 70 degree C.



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
sci-dynabeads-ip-2
