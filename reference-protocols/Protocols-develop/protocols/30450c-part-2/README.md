# BioLegend Human IL-2 ELISA MAX Deluxe Set: Add Samples and Standards to ELISA Plates

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol uses 8-channel P300 and p20 pipettes to transfer samples and standard dilutions to a batch of 1-5 ELISA plates for the attached BioLegend Human IL-2 ELISA. User-determined parameters are available to specify the number of ELISA plates (1-5), to include or not include a tip touch following dispenses, the aspiration position in the large reservoir (in millimeters above the labware bottom), and to automate or not automate the placement and replenishment of tips in row H of the empty tip box in slot 9 (these tips will be used to transfer standard from row H of the sample plate to row H of the ELISA plate).

Links:
* [BioLegend Human IL-2 ELISA MAX Deluxe Set - user manual](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/30450c/431804_R7_Human_IL-2_Deluxe+1.pdf)


---



### Labware
* Opentrons Tips for the p300 and p20 (https://shop.opentrons.com)
* [Nest 195 mL Reservoir](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir)
* [Corning 96 Well Plate 360 µL Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)



### Pipettes
* P300 multi-channel Opentrons Gen2 Pipette - (https://shop.opentrons.com)
* P20 multi-channel Opentrons Gen2 Pipette - (https://shop.opentrons.com)

### Reagents
[BioLegend Human IL-2 ELISA MAX Deluxe Set - user manual](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/30450c/431804_R7_Human_IL-2_Deluxe+1.pdf)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/30450c/screenshot2-deck.png)
</br>
</br>
**Slots 1-5**: ELISA plates </br>
**Slot 7**: Reagent Reservoir (195 mL Nest reservoir) </br>
![reservoir layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/30450c/screenshot2-reservoir.png)
</br>
</br>
**Slot 8**: Sample Plate (96-Well PCR plate) </br>
![sample plate layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/30450c/screenshot2-sampleplate.png)
</br>
</br>
**Slot 9**: Empty Opentrons 300 uL tip box </br>
**Slot 10**: Opentrons 20 uL tips </br>
**Slot 11**: Opentrons 300 uL tips </br>


---

### Protocol Steps
1. The robot will pause and prompt the user to ensure that 20 uL tips and the current sample plate are on deck.
2. The p300 will pick up 7 tips and transfer 90 uL 1x Assay Diluent A to rows A-G of the current ELISA plate and return the tips to the box to be used for the next plate.
3. The p300 will load row H of the empty tip box in slot 9 with tips (using columns 2-12 of the slot 11 tip box as source).
4. The p300 will transfer 100 uL of standards from row H of the sample plate to row H of the current ELISA plate using 1-tip on the front-most channel.
5. The p20 will transfer 10 uL of sample to rows A-G of the current ELISA plate.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
30450c-part-2
