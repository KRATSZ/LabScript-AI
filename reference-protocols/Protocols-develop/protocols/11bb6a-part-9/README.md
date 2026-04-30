# Quarter Volume Library Prep Step 9: Fragment Analyzer

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* NEBNext

## Description
This protocol uses multi-channel P20 and P300 pipettes to perform fragment analyzer set up steps on 48-96 output libraries. User-determined parameters are available for selection of the labware for the libraries plate.

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
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11bb6a/screenshot9-deck-corrected.png)
</br>
</br>
**Slot 1**: Opentrons Temperature Module empty </br>
**Slot 3**: Libraries Plate (dropdown selected 96-well PCR plate) </br>
**Slot 5**: Reagent Reservoir (Nest 12-well 15 mL reservoir) </br>
**Slot 6**: Fragment Analyzer Plate on Opentrons 96-Well Aluminum Block (biorad_96_fragment_analyzer_plate_aluminumblock_200ul) </br>
**Slot 9**: Opentrons Magnetic Module empty </br>
**Slot 10**: Opentrons 20 uL filter tips </br>
**Slot 7**: Opentrons 200 uL filter tips </br>


---

### Protocol Steps
1. The protocol will alert the user to ensure reagents are present on deck in sufficient volume.
2. The p300 multi will deliver diluent buffer to wells of the fragment analyzer plate (all wells except H12).
3. The p20 multi will transfer 2 uL library sample from the libraries plate to the fragment analyzer plate.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
11bb6a-part-9
