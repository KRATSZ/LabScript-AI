# Automated Sample Prep for GNA Octea [v2]

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Covid

## Description
This protocol automates GNA Octea prep. Using the [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) and the [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette), all the reagents necessary for the sample prep are transferred to the samples and the samples are incubated on the [Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) and [Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck). Once all sample prep has been completed, the samples are transferred to a custom plate containing the labware needed to test the samples on the [GNA analyzer](https://www.gna-bio.com/products/).

This protocol is still a work in progress and will be updated.


Explanation of complex parameters below:
* **P300-Multi Mount**: Select which mount the [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) is attached to.
* **P300-Single Mount**: Select which mount the [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) is attached to.
* **Labware on Temp Deck + Al Block**: Select which tube type will contain the samples.
* **Reconstitue MagBeads/PCA?**: Specify whether the OT-2 will reconstitute the MagBeads and PCA.


---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [NEST 96-Deep Well Plate, 2mL](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* 1.5mL (and/or 2mL) [Microcentrigue Tubes]()
* Custom Plate for GNA Octea Chip

### Pipettes
* [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

### Reagents
* WB1
* RS1
* HB1
* Lyophilized MagBeads
* Lyophilized PCA Mix

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/gna_octea/gnaV2deck.png)

### Reagent Setup
[NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (Deck Slot 10)
* Well 12: HB1
* Well 10: HB1
* Well 1: Liquid Waste (Empty)
![Reservoir Layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/gna_octea/gnaV2res.png)
</br>
[Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) (Deck Slot 6)
* A1: Magnetic Beads
* A6: PCA
* D6: RS1, is using
![Rack layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/gna_octea/gnaV2rack.png)

---

### Protocol Steps
1. The protocol begins with the Single-Channel Pipette transferring 10µL of Magnetic Beads to the 8 samples. The Magnetic Beads are mixed before aspiration and RS1 is added if selected above. The same tip is used for all transfers.
2. The Single-Channel Pipette picks up a tip, transfers 680µL HB1 (170µL, 4x) to the sample, mixes 10 times, performs a touch tip, then drops tip in waste (for each sample).
3. The Temperature Module is set to 80C and the protocol delays for 3 minutes (incubation).
4. The Temperature Module is set to 56C. While the Temperature Module is cooling, the Single-Channel Pipette will mix the samples.
5. After a 3 minute incubation at 56C, the Single-Channel Pipette will transfer samples to the Deepwell Plate on the Magnetic Module
6. The Magnetic Module will engage and the protocol will delay for 2 minutes (incubation). After the delay, the Multi-Channel Pipette will transfer the supernatant (160µL, 5x) to A1 of the 12-Well Reservoir.
7. The Multi-Channel Pipette, using new tips, will transfer 200µl of WB1 and mix 12 times.
8. Again, the Magnetic Module will engage and the protocol will delay for 2 minutes (incubation). After the delay, the Multi-Channel Pipette will transfer the supernatant (200µL) to A1 of the 12-Well Reservoir.
9. The Single-Channel Pipette, using a single tip, will transfer 40µL of PCA to each of the sample wells in the Deepwell Plate, reconstituting the PCA beforehand if selected.
10. Using a new tip for each sample, the Single-Channel Pipette will mix the sample and transfer 40µL to the GNA Octea well.


### Process
1. Input your protocol parameters above.
2. Download your protocol.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions), if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
gna_octea_v2
