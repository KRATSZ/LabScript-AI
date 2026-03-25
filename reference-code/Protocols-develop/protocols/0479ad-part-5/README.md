# NEBNext Ultra II RNA Library Prep Kit for Illumina: E7770S Section 1 with Poly(A) Isolation using Oligo-dT Beads: Part-5 - Bead Purification of Ligation Reaction

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* NEBNext Ultra II RNA Library Prep Kit for Illumina

## Description
This protocol uses multi-channel P20 and P300 pipettes to perform library prep steps on 8-48 input total RNA samples according to the attached NEB user guide. This is part-5 of a six part process (bead purification of the ligation reaction). User-determined parameters are available to specify the number of samples and the magnet engage height and time.


---


### Labware
* [Opentrons Filter Tips for the P20 and P300] (https://shop.opentrons.com)
* [Opentrons Temperature Module] (https://shop.opentrons.com/modules/)
* [Opentrons Magnetic Module] (https://shop.opentrons.com/modules/)
* [USA Scientific 12 Well Reservoir 22 mL] (https://shop.opentrons.com)
* ThermoFisher 96 Well PCR Plate 300 uL Semi-Skirted


### Pipettes
* Opentrons multi-channel P300 and p20 Gen2 Pipettes (https://shop.opentrons.com/pipettes/)

### Reagents
* [NEB User Guide] (https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad/manualE7770.pdf)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad/screenshot5-deck.png)
</br>
</br>
**Slot 1**: Opentrons Temperature Module with 96-Well Aluminum Block holding Output Plate (ThermoFisher 96 Well PCR Plate 300 uL Semi-Skirted) </br>
**Slot 2**: Reagent Reservoir for NEBNext Sample Purification Beads, 0.1X TE, 80 Percent EtOH, Liquid Waste (usascientific_12_reservoir_22ml) </br>
![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad/screenshot5-reservoir.png)
</br>
</br>
**Slot 4**: Opentrons Temperature Module empty </br>
**Slot 9**: Opentrons Magnetic Module (ThermoFisher 96 Well PCR Plate 300 uL Semi-Skirted on Custom Plastic Adapter containing 96 uL Adapter-Ligated cDNA Samples) </br>
![magmod](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad/screenshot5-magmod.png)
</br>
</br>
**Slot 8**: Opentrons 20 uL filter tips </br>
**Slots 6,7,10**: Opentrons 200 uL filter tips </br>


---

### Protocol Steps
1. Use settings in the OT app to pre-cool the temperature module in slot 1 to 4 degrees C prior to running this protocol.
2. The protocol will alert the user to ensure reagents are present on deck in sufficient volume.
3. The p300 multi will add NEBNext Sample Purification Beads to the adapter-ligated cDNA samples in the magnetic module plate and mix.
4. The OT-2 will wait 10 minutes for an on-deck incubation.
5. The magnets will engage to pellet the beads. The p300 multi will remove and discard the supernatant.
6. The p300 multi will wash the bead pellets twice with 80 percent ethanol.
7. The OT-2 will wait for the bead pellets to air dry.
8. The magnets will disengage for elution.
9. The p20 multi will add 0.1X TE and mix to resuspend the beads.
10. The magnets will engage to pellet the beads.
11. The p20 multi will recover the eluate to the output plate.


### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0479ad-part-5
