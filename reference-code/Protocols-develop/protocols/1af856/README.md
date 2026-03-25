# Lexogen QuantSeq-Pool Sample-Barcoded 3-Prime mRNA-Seq Library Prep Kit for Illumina

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* Lexogen

## Description
This protocol uses single-channel P20 and P300 pipettes to perform library prep steps on 8-96 input samples according to the attached experimental protocol and Lexogen user guide. User-determined parameters are available to specify the number of samples, the bead drying time and the magnet engage time.


---


### Labware
* [Opentrons Filter Tips for the P20 and P300] (https://shop.opentrons.com)
* [Opentrons Temperature Module] (https://shop.opentrons.com/modules/)
* [Opentrons Magnetic Module] (https://shop.opentrons.com/modules/)
* [Opentrons 4-in-1 Tuberack, Nest Well Plates, Nest Reservoir] (https://shop.opentrons.com)


### Pipettes
* Opentrons single-channel P20 and P300 Gen2 Pipettes (https://shop.opentrons.com/pipettes/)

### Reagents
* [Lexogen User Guide] (https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1af856/QSP+Manual+User+Protocol.pdf)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1af856/screenshot0823-deck.png)
</br>
</br>
**Slot 1**: Final Output Plate (nest_96_wellplate_100ul_pcr_full_skirt) </br>
**Slot 2**: Tube Rack for Reagents (opentrons_24_tuberack_nest_1.5ml_snapcap) </br>
![tuberack](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1af856/screenshot0823-tuberack.png)
</br>
</br>
**Slot 3**: 80 Percent Ethanol Reservoir (nest_12_reservoir_15ml) </br>
**Slot 4**: Opentrons Magnetic Module with 96-Deep Well Plate (nest_96_wellplate_2ml_deep) </br>
**Slot 5**: PCR Plate (nest_96_wellplate_100ul_pcr_full_skirt) </br>
**Slot 7**: Opentrons Temperature Module with 24-Well Aluminum Block holding 1.5 mL Nest SnapCap Tubes </br>
![tempmod](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1af856/screenshot0823-block.png)
</br>
</br>
**Slot 8**: Index Plate </br>
**Slots 10,11**: Opentrons 20 uL filter tips </br>
**Slots 6,9**: Opentrons 200 uL filter tips </br>


---

### Protocol Steps
1. Use settings in the OT app to pre-cool the temperature module to 4 degrees C prior to running this protocol.
2. The protocol will alert the user to ensure reagents are present on deck in sufficient volume.
3. The protocol will prompt the user to manually add 10-120 ng total RNA in 7 uL to dried-in sample-barcode RT primer in 8-96 wells of the index plate in slot 8, mix to dissolve the primer, incubate 3 minutes 85 degrees C, cool to 25 degrees C, spin and return the plate to slot 8.
4. The p20 single and p300 single are used to assemble a reverse transcription mastermix and add 3 uL of it to each filled well in the index plate.
5. After a 15 minute, off-deck incubation at 42 degrees C, reactions are pooled into one or two wells (if more than 56 samples) of the magnetic module plate followed by a bead cleanup.
6. Eluates are combined into a single pool and treated with RNA removal solution followed by second-strand synthesis and a second bead cleanup.
7. The p20 single will assemble and add PCR mastermix.
8. The protocol will pause for off-deck PCR library amplification followed by a final bead cleanup.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
1af856
