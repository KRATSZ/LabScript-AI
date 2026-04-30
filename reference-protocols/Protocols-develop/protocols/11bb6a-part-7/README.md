# Quarter Volume Library Prep Step 7: PCR Enrichment

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* NEBNext

## Description
This protocol uses multi-channel P20 and P300 pipettes to perform PCR enrichment setup steps on 48-96 input samples. User-determined parameters are available for selection of the i7 primer plate row, the i5 primer plate column, sample count, and labware.

Links:
* [Part 1: Enzymatic Fragmentation and End Prep](http://protocols.opentrons.com/protocol/11bb6a)
* [Part 2: Sample Cleanup for Covaris Samples](http://protocols.opentrons.com/protocol/11bb6a-part-2)
* [Part 3: End Prep](http://protocols.opentrons.com/protocol/11bb6a-part-3)
* [Part 4: Adapter Ligation](http://protocols.opentrons.com/protocol/11bb6a-part-4)
* [Part 5: Size Selection](http://protocols.opentrons.com/protocol/11bb6a-part-5)
* [Part 6: Clean Up](http://protocols.opentrons.com/protocol/11bb6a-part-6)
* [Part 7: PCR Enrichment](http://protocols.opentrons.com/protocol/11bb6a-part-7)
* [Part 8: Sample Clean Up](http://protocols.opentrons.com/protocol/11bb6a-part-8)
* [Part 9: Fragment Analyzer](http://protocols.opentrons.com/protocol/11bb6a-part-9)
* [Part 10: Pooling According to Concentration](http://protocols.opentrons.com/protocol/11bb6a-part-10)

---


### Labware
* [Opentrons Filter Tips for the P20 and P300] (https://shop.opentrons.com)
* [Opentrons Temperature Module] (https://shop.opentrons.com/modules/)
* [Opentrons Magnetic Module] (https://shop.opentrons.com/modules/)
* [Selected 96-well PCR plate] ([see parameter dropdown list below] https://labware.opentrons.com/)


### Pipettes
* Opentrons 8-channel P20 and P300 Gen2 Pipettes (https://shop.opentrons.com/pipettes/)

### Reagents
* [NEBNext® Ultra™ II DNA Library Prep Kit for Illumina, Catalog # E7645S / E7645L] (https://international.neb.com/products/e7645-nebnext-ultra-ii-dna-library-prep-kit-for-illumina#Product%20Information)
* [NEBNext® Ultra™ II FS DNA Library Prep Kit for Illumina, Catalog # E7805S / E7805L] (https://international.neb.com/products/e7805-nebnext-ultra-ii-fs-dna-library-prep-kit-for-illumina#Product%20Information)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11bb6a/screenshot7-deck.png)
</br>
</br>
**Slot 1**: Opentrons Temperature Module (dropdown-selected aluminum block and tube combination) </br>
![tempmod layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11bb6a/screenshot7-tempmod.png)
</br>
</br>
**Slot 2**: i5 indexes (eppendorf_96_wellplate_200ul) </br>
**Slot 5**: i7 indexes (eppendorf_96_wellplate_200ul) </br>
**Slot 8**: PCR plate (dropdown-selected 96-well PCR plate) </br>
**Slot 9**: Opentrons Magnetic Module with library prep plate or size plate (dropdown-selected 96-well PCR plate) </br>
**Slots 10,3,6**: Opentrons 20 uL filter tips </br>
**Slot 11**: Opentrons 200 uL filter tips </br>


---

### Protocol Steps
1. Before running this protocol with custom labware on the magnetic module, an engage height for this labware must be entered as a parameter value below.
2. Before running this protocol, use settings in the OT app to pre-cool the temperature module to 4 degrees C.
3. The protocol will alert the user to ensure reagents are present on deck in sufficient volume.
4. The p20 multi will use 1 tip on the rear-most channel to deliver i7 indexes from the specified row to columns of the PCR plate.
5. The p300 multi will use 1 tip on the rear-most channel to deliver Q5 Mastermix to the 6th column of the reagent plate.
6. The p20 multi will transfer Q5 Mastermix from the reagent plate (column 6) to columns of the PCR plate.
7. The p20 multi will transfer i5 indexes from the specified column to columns of the PCR plate.
8. The p20 multi will transfer eluted sample from columns of the magnetic module plate to columns of the PCR plate.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
11bb6a-part-7
