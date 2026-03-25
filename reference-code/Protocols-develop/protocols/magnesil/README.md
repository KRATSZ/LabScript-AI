# Promega MagneSil Purification

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Nucleic Acid Extraction & Purification
	* MagneSil

## Description
This protocol performs a nucleic acid purification protocol based on the MagneSil Plasmid Purification System from Promega. Using flexible parameters (described below), one can adapt this protocol to the equipment in their lab and modify to their workflow.


Explanation of complex parameters below:
* **Number of Samples**: Specify the number of samples (1-32)
* **Pipette Model**: Select between the GEN1 and GEN2 [P300 8-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)
* **Pipette Mount**: Select which mount (Right, Left) the pipette is attached to
* **Use Filter Tips?**: Select whether to use [Opentrons 200µL Filter Tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/) or [Opentrons 300µL Standard Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)
* **Magnetic Module Model**: Select between the GEN1 and GEN2 [Opentrons Magnetic Module](https://shop.opentrons.com/magnetic-module-gen2/)
* **Sample Plate Type**: Select the type of plate containing samples (will be placed on Magnetic Module)
* **Reservoir Type**: Select which 12-Well Reservoir will be used to hold reagents
* **Elution Plate Type**: Select the type of plate that will be used for the elutions


---

### Modules
[Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)


### Labware
* Opentrons Tips for P300 ([Filter](https://shop.opentrons.com/opentrons-200ul-filter-tips/) or [Standard](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/))
* 96-Deepwell Plate (containing samples) ([Example](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/))
* 12-Well Reservoir ([Example](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/))
* 96-Well Plate ([Example](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/))


### Pipettes
[P300 8-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
Promega MagneSil

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/magnesil/magnesil_deck.png)
</br>
</br>
**Slot 2**: 12-Well Reservoir (See Reagent Setup below for more information)</br>
</br>
**Slot 4**: [Opentrons Magnetic Module](https://shop.opentrons.com/magnetic-module-gen2/) with 96-Deepwell Plate containing samples in odd columns (during the protocol, samples will be transferred to the even columns)</br>
![plate layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/magnesil/magnesil_plate.png)
</br>
**Slot 6**: 96-Well Plate for elutes</br>
</br>
**Slots 7-11**: Opentrons Tips (Each column of samples requires 15 columns of tips)

### Reagent Setup
* This section can contain finer detail and images describing reagent volumes and positioning in their respective labware. Examples:
* Slot 2: 12-Well Reservoir
![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/magnesil/magnesil_reservoir.png)

---

### Protocol Steps
1. 90µL of Resuspension Buffer is added to each column of samples.
2. 120µL of Lysis Solution is added to each column of samples.
3. Two minute incubation.
4. 120µL of Neutralization Buffer is added to each column of samples.
5. 30µL of MagneSil Blue is added to each column of samples.
6. Magnets engage; 10 minute incubation.
7. 250µL of sample is transferred to corresponding even-numbered column in the same plate.
8. Magnets disengage.
9. 50µL of MagneSil Red is added to each column of samples.
10. Magnets engage; 10 minute incubation.
11. 300µL is discarded in corresponding columns of 12-Well Reservoir for liquid waste.
12. Magnets disengage.
13. 100µL of Ethanol is added to each column of samples.
14. Magnets engage; 2 minute incubation.
15. 100µL is discarded in corresponding columns of 12-Well Reservoir for liquid waste.
16. Magnets disengage.
17. Steps 13-16 are repeated two more times for a total of three washes.
18. 10 minute drying.
19. User is alerted to check for elution plate.
20. 100µL of Elution Buffer is added to each column of samples.
21. Magnets engage; 10 minute incubation.
22. 100µL of elutes are transferred from each column to column of elution plate.
23. The end.

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
magnesil
