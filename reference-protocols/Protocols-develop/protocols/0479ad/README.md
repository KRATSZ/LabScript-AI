# NEBNext Ultra II RNA Library Prep Kit for Illumina: E7770S Section 1 with Poly(A) Isolation using Oligo-dT Beads: Part-1 - Poly(A) RNA Isolation, Fragmentation and Priming

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* NEBNext Ultra II RNA Library Prep Kit for Illumina

## Description
This protocol uses multi-channel P20 and P300 pipettes to perform library prep steps on 8-48 input total RNA samples according to the attached NEB user guide (reagents were combined in a few instances to reduce the number of transfer steps required). User-determined parameters are available to specify the number of samples and the magnet engage height and time.


---


### Labware
* [Opentrons Filter Tips for the P20 and P300] (https://shop.opentrons.com)
* [Opentrons Temperature Module] (https://shop.opentrons.com/modules/)
* [Opentrons Magnetic Module] (https://shop.opentrons.com/modules/)
* [Nest 96 Well PCR Plates 100 uL, USA Scientific 12 Well Reservoir 22 mL] (https://shop.opentrons.com)
* ThermoFisher 96 Well PCR Plate 300 uL Semi-Skirted


### Pipettes
* Opentrons multi-channel P20 and P300 Gen2 Pipettes (https://shop.opentrons.com/pipettes/)

### Reagents
* [NEB User Guide] (https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad/manualE7770.pdf)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad/Screen+Shot+2022-10-06+at+1.41.27+PM.png)
</br>
</br>
**Slot 1**: Opentrons Temperature Module with 96-Well Aluminum Block holding Reagent Plate (nest_96_wellplate_100ul_pcr_full_skirt) </br>
![tempmod](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad/Screen+Shot+2022-10-06+at+1.43.49+PM.png)
</br>
</br>
**Slot 2**: Reagent Reservoir for 0.1X TE, Wash Buffer, Liquid Waste (usascientific_12_reservoir_22ml) </br>
![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad/Screen+Shot+2022-10-06+at+1.42.58+PM.png)
</br>
</br>
**Slot 4**: Opentrons Temperature Module with 96-Well Aluminum Block holding Output Plate (ThermoFisher 96 Well PCR Plate 300 uL Semi-Skirted) </br>
**Slot 9**: Opentrons Magnetic Module (ThermoFisher 96 Well PCR Plate 300 uL Semi-Skirted on Custom Plastic Adapter containing 50 uL Total RNA Samples + 50 uL Oligo-dT Beads) </br>
![magmod](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad/Screen+Shot+2022-10-06+at+1.42.39+PM.png)
</br>
</br>
**Slot 8**: Opentrons 20 uL filter tips </br>
**Slots 6,7,10,11**: Opentrons 200 uL filter tips </br>


---

### Protocol Steps
1. Use settings in the OT app to pre-cool the temperature modules to 4 degrees C prior to running this protocol.
2. The protocol will alert the user to ensure reagents are present on deck in sufficient volume.
3. The p300 multi will mix the total RNA samples and oligo-dT beads.
4. The OT-2 will pause for an off-deck incubation.
5. The p300 multi will mix the total RNA samples and oligo-dT beads.
6. The magnets will engage to pellet the beads. The p300 multi will remove and discard the supernatant.
7. The p300 multi will wash the bead pellets twice with wash buffer.
8. The p300 multi will add 0.1X TE and mix to resuspend the beads.
9. The OT-2 will pause for an off-deck incubation.
10. The p300 multi will add binding buffer to the beads and mix.
11. The magnets will engage to pellet the beads. The p300 multi will remove and discard the supernatant.
12. The p300 multi will wash the bead pellets with wash buffer.
13. The p20 multi will add first strand reaction buffer + random primer to elute the mRNA.
14. The OT-2 will pause for an off-deck incubation.
15. The magnets will engage to pellet the beads. The p20 multi will transfer the elute to the output plate.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0479ad
