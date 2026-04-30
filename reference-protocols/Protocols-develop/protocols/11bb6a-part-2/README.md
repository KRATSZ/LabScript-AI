# Quarter Volume Library Prep Step 2: Sample Cleanup for Covaris Samples

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* NEBNext

## Description
This protocol uses multi-channel P20 and P300 pipettes to perform bead-based sample cleanup steps on 48-96 input samples. User-determined parameters are available for selection of the labware for the 96-well PCR plate on the magnetic module, the sample volume, and the bead ratio.

---


### Labware
* Opentrons Filter Tips for the P20 and P300 (https://shop.opentrons.com)
* Opentrons Temperature Module (https://shop.opentrons.com/modules/)
* Opentrons Magnetic Module (https://shop.opentrons.com/modules/)
* Selected 96-well PCR plate ([see parameter dropdown list below] https://labware.opentrons.com/)


### Pipettes
* Opentrons 8-channel P20 and P300 Gen2 Pipettes (https://shop.opentrons.com/pipettes/)

### Reagents
* NEBNext® Ultra™ II DNA Library Prep Kit for Illumina, Catalog # E7645S / E7645L (https://international.neb.com/products/e7645-nebnext-ultra-ii-dna-library-prep-kit-for-illumina#Product%20Information)
* NEBNext® Ultra™ II FS DNA Library Prep Kit for Illumina, Catalog # E7805S / E7805L (https://international.neb.com/products/e7805-nebnext-ultra-ii-fs-dna-library-prep-kit-for-illumina#Product%20Information)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11bb6a/screenshot2-deck.png)
</br>
</br>
**Slot 1**: Opentrons Temperature Module empty </br>
**Slot 5**: Reagent Reservoir (Nest 12-well 15 mL reservoir) </br>
![reservoir layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11bb6a/screenshot2-reservoir.png)
</br>
</br>
**Slot 6**: Ethanol (Agilent 290 mL reservoir) </br>
**Slot 8**: Liquid Waste (Agilent 290 mL reservoir) </br>
**Slot 9**: Magnetic Module with dropdown-selected 96-well PCR plate </br>
**Slot 10**: Opentrons 20 uL filter tips </br>
**Slots 2,3,4,7,11**: Opentrons 200 uL filter tips </br>


---

### Protocol Steps
1. Before running this protocol with custom labware on the magnetic module, an engage height for this labware must be entered as a parameter value below.
2. The protocol will alert the user to ensure beads, TE and ethanol are present on deck in sufficient volume.
3. The p300 multi will deliver beads to the magnetic module plate and mix.
4. After an incubation and magnet engagement, the p300 multi will remove and discard bead pellet supernatants.
5. The p300 multi will perform two 80 percent ethanol washes of the bead pellets.
6. After air drying of bead pellets, the p20 multi will resuspend the beads in 1x TE and mix.
7. After an incubation, magnets are engaged.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
11bb6a-part-2
