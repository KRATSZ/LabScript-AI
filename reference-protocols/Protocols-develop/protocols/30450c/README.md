# BioLegend Human IL-2 ELISA MAX Deluxe Set: Add Reagent to ELISA Plates

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling

## Description

This protocol uses an 8-channel P300 pipette to add 100 or 200 uL of reagent to a batch of 1-5 ELISA plates for steps of the attached BioLegend Human IL-2 ELISA. User-determined parameters are available to specify which step of the ELISA process is being performed (coating, blocking, detection antibody, avidin HRP, TMB substrate or stop step), the number of ELISA plates (1-5), the aspiration position in the large reservoir (in millimeters above the labware bottom), to optionally pause the robot with the P300 above the reagent reservoir to wait for off-deck plate washing steps, and to include or not include a tip touch following reagent dispenses.

Links:
* [BioLegend Human IL-2 ELISA MAX Deluxe Set - user manual](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/30450c/431804_R7_Human_IL-2_Deluxe+1.pdf)


---



### Labware
* Opentrons Tips for the p300 (https://shop.opentrons.com)
* [Nest 195 mL Reservoir](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir)
* [Corning 96 Well Plate 360 µL Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)



### Pipettes
* P300 multi-channel Opentrons Gen2 Pipette - (https://shop.opentrons.com)

### Reagents
[BioLegend Human IL-2 ELISA MAX Deluxe Set - user manual](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/30450c/431804_R7_Human_IL-2_Deluxe+1.pdf)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/30450c/screenshot-deck.png)
</br>
</br>
**Slots 1-5**: ELISA plates </br>
**Slot 10**: Reagent Reservoir (195 mL Nest reservoir) </br>
**Slot 11**: Opentrons 300 uL tips </br>


---

### Protocol Steps
1. (Optional) The p300 will move to the reservoir and pause, waiting for the user to complete off-deck washing steps.
2. The p300 will transfer 100 or 200 uL reagent to ELISA plate wells.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
30450c
