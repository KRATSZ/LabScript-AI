# NEBNext Ultra II RNA Library Prep Kit for Illumina: E7770S Section 1 with Poly(A) Isolation using Oligo-dT Beads: Part-4 - End Prep and Adapter Ligation

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* NEBNext Ultra II RNA Library Prep Kit for Illumina

## Description
This protocol uses multi-channel P20 and P300 pipettes to perform library prep steps on 8-48 input total RNA samples according to the attached NEB user guide. This is part-4 of a six part process (Part-4 - End Prep and Adapter Ligation). End prep reaction buffer + end prep enzyme mix are combined into a single mix to reduce the number of transfer steps. A user-specified parameter is available to specify the number of samples in the current run.


---


### Labware
* [Opentrons Filter Tips for the P20 and P300] (https://shop.opentrons.com)
* [Opentrons Temperature Module] (https://shop.opentrons.com/modules/)
* [Opentrons Magnetic Module] (https://shop.opentrons.com/modules/)
* ThermoFisher 96 Well PCR Plate 300 uL Semi-Skirted


### Pipettes
* Opentrons multi-channel P20 and P300 Gen2 Pipettes (https://shop.opentrons.com/pipettes/)

### Reagents
* [NEB User Guide] (https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad/manualE7770.pdf)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/screenshot4-deck.png)
</br>
</br>
**Slot 1**: Opentrons Temperature Module with 96-Well Aluminum Block holding cDNA Plate (ThermoFisher 96 Well PCR Plate 300 uL Semi-Skirted) </br>
![tempmod](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/screenshot4-tempmod.png)
</br>
</br>
**Slot 4**: Opentrons Temperature Module with 96-Well Aluminum Block holding Reagent Plate (nest_96_wellplate_100ul_pcr_full_skirt) </br>
![tempmod2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/screenshot4-tempmod2.png)
</br>
</br>
**Slot 9**: Opentrons Magnetic Module (empty) </br>
**Slots 5,7**: Opentrons 20 uL filter tips </br>
**Slot 6**: Opentrons 200 uL filter tips </br>


---

### Protocol Steps
1. Use settings in the OT app to pre-cool the temperature modules to 4 degrees C prior to running this protocol.
2. The protocol will alert the user to ensure reagents are present on deck in sufficient volume.
3. The p20 multi will add 10 uL end prep mix (end prep reaction buffer + end prep enzyme mix) to the cDNA samples and and mix.
4. The OT-2 will pause for an off-deck incubation.
5. The p20 multi will add 2.5 uL diluted adapter to the cDNA samples.
6. The p300 multi will add 31 uL ligation master mix + ligation enhancer to the cDNA samples and mix.
7. The OT-2 will pause for an off-deck incubation.
8. The p20 multi will add 3 uL user enzyme to the cDNA samples and mix.
9. The OT-2 will finish part-4 notifying the user to proceed with an off-deck incubation.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0479ad-part-4
