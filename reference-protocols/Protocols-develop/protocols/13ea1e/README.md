# Extraction Prep with Kingfisher Flex Extractor

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Partner Name](partner website link)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps a sample plate as well as an ethanol, NPW3, NPW4, and elution buffer plate for further use in a Kingfisher Flex Extractor. Samples are pre-loaded onto the sample plate before the protocol begins. Mag beads are then added to sample, and after an incubation step, all other reagent plates are prepped.  

The protocol is broken down into 3 main parts:
* Controls are added to sample plate
* Proteinase K is added to samples
* Magnetic Beads are added, incubate
* Sample blocks made

Note: For all transfers between reservoirs/tubes to well plate, transfers will always iterate over all wells in the source. For example, magnetic beads will be transferred from A1 to plate, A2 to plate, A3 to plate, A4 to plate, A1 to plate, etc. Consequently, all reaction volumes should be split equally into respective wells as seen in the deck layout.

Explanation of complex parameters below:
* `Number of samples`: Specify the number of populated wells (1-96, include controls) that the sample block, elution buffer block, ethanol block, NPW3 block, and NPW4 block will be filled.
* `Mix repetitions to resuspend beads`: Specify the amount of mix steps to re-suspend beads each time the pipette returns to the reservoir.
* `P1000 Single Channel Mount (GEN2)`: Specify which mount the P1000 Single Channel pipette will be mounted.
* `P300 Multi Channel Mount (GEN2)`: Specify which mount the P300 Multi Channel pipette will be mounted.
---

### Labware
* Kingfisher 96 Well Plate
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 4-in-1 tube rack with 1.5mL tubes](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)

### Pipettes
* [P1000 GEN2 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P300 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)


---

### Deck Setup
* Deck setup with samples loaded into all wells except A1 and B1.

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/13ea1e/pt1/Screen+Shot+2021-05-26+at+11.24.55+AM.png)

### Reagent Setup

* Reservoir 1: Slot 1

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/13ea1e/pt1/Screen+Shot+2021-05-24+at+9.08.52+AM.png)
* Reservoir 2: Slot 2

![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/13ea1e/pt1/Screen+Shot+2021-05-24+at+9.14.53+AM.png)
* Tube rack: Slot 11

![tube rack](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/13ea1e/pt1/Screen+Shot+2021-05-24+at+9.09.13+AM.png)

---

### Protocol Steps
1. Controls are added to sample plate
2. Proteinase K is added to samples
3. Magnetic beads are added to samples
4. Incubate 15 minutes
5. Ethanol block is prepped.
6. NPW3 block is prepped.
7. NPW4 block is prepped.
10. Elution buffer block is prepped.

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
13ea1e
