# KingFisher Flex Plate Set Up

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol uses 8-channel P20 and P300 pipettes to add a fixed volume (10, 1000, 1000, 500, and 100 uL) of a specific reagent (Proteinase K Solution, Wash Buffer, 80 Percent EtOH, 80 Percent EtOH, and Elution Solution) to the corresponding processing plate on the OT-2 deck (Sample Plate, Wash 1 Plate, Wash 2 Plate, Wash 3 Plate, and Elution Plate). User-determined parameters are available to specify the number of columns to be filled in the five processing plates and the labware to be used for the processing plate, the wash buffer reservoir, the EtOH reservoir, and the 12-well reservoir holding the Proteinase K Solution and Elution Solution.

Links:
* [Experimental Protocol](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4e4c0c/Opentrons+Protocol+to+code.docx)


---



### Labware
* Opentrons Filter Tips for the p300 and p20 (https://shop.opentrons.com)
* [Nest 195 mL Reservoir](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir)
* [Nest 12-Well Reservoir](https://shop.opentrons.com/verified-labware/)
* [Nest 96-Deep Well Plate 2 mL](https://shop.opentrons.com/verified-labware/)



### Pipettes
* P300 and P20 multi-channel Opentrons Gen2 Pipette - (https://shop.opentrons.com)

### Reagents
* Proteinase K Solution
* Wash Buffer
* 80 Percent Ethanol
* Elution Solution

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4e4c0c/Screen+Shot+2023-02-06+at+3.55.47+PM.png)
</br>
</br>
**Slots 1-5**: Processing Plates (Sample Plate, Wash 1 Plate, Wash 2 plate, Wash 3 Plate, Elution Plate) (Nest 2 96-Deep Well 2 mL) </br>
**Slot 7**: 12-Well Reagent Reservoir (Nest 12-Well Reservoir) </br>
![reservoir layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4e4c0c/Screen+Shot+2023-02-06+at+3.56.24+PM.png)
</br>
</br>
**Slot 8**: 80 Percent EtOH Reservoir (Nest 195 mL Reservoir) </br>
**Slot 9**: Wash Buffer Reservoir (Nest 195 mL Reservoir) </br>
**Slot 10**: Opentrons 20 uL Filter Tips </br>
**Slot 11**: Opentrons 200 uL Filter Tips </br>


---

### Protocol Steps
1. The p20 will pick up tips, add 10 uL Proteinase K Solution to the user-selected number of columns in the Sample Plate, then drop the tips.
2. The p300 will pick up tips, transfer 1000 uL Wash Buffer to the user-selected number of columns in the Wash 1 Plate, then drop the tips.
3. The p300 will pick up tips, transfer 1000 uL 80 Percent Ethanol to the user-selected number of columns in the Wash 2 Plate, then drop the tips.
4. The p300 will pick up tips, transfer 500 uL 80 Percent Ethanol to the user-selected number of columns in the Wash 3 Plate, then drop the tips.
5. The p300 will pick up tips, transfer 100 uL Elution Solution to the user-selected number of columns in the Elution Plate, then drop the tips.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4e4c0c
