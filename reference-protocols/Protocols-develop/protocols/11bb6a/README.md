# Quarter Volume Library Prep Step 1: Enzymatic Fragmentation and End Prep

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* NEBNext

## Description
This protocol uses multi-channel P20 and P300 pipettes to perform enzymatic fragmentation and end prep steps on 48-96 input samples. User-determined parameters are available for selection of the labware for the 96-well library prep and reagent plates and the aluminum block and tube combination holding reagents on the temperature module.

---


### Labware
* Opentrons Filter Tips for the P20 and P300 (https://shop.opentrons.com)
* Opentrons Temperature Module (https://shop.opentrons.com/modules/)
* Selected 96-well PCR plate ([see parameter dropdown list below] https://labware.opentrons.com/)
* Selected 24-well Aluminum Block and Tube Combination ([see parameter dropdown list below] https://labware.opentrons.com/)


### Pipettes
* Opentrons 8-channel P20 and P300 Gen2 Pipettes (https://shop.opentrons.com/pipettes/)

### Reagents
* NEBNext® Ultra™ II DNA Library Prep Kit for Illumina, Catalog # E7645S / E7645L (https://international.neb.com/products/e7645-nebnext-ultra-ii-dna-library-prep-kit-for-illumina#Product%20Information)
* NEBNext® Ultra™ II FS DNA Library Prep Kit for Illumina, Catalog # E7805S / E7805L (https://international.neb.com/products/e7805-nebnext-ultra-ii-fs-dna-library-prep-kit-for-illumina#Product%20Information)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11bb6a/screenshot1-deck.png)
</br>
</br>
**Slot 1**: Opentrons Temperature Module with dropdown-selected 24-well Aluminum Block and Tube combination </br>
![temperature module layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11bb6a/screenshot1-tempmod.png)
</br>
</br>
**Slot 3**: Library Prep Plate (dropdown-selected 96-well PCR plate) </br>
**Slot 6**: Reagent Plate (dropdown-selected 96-well PCR plate) </br>
**Slot 10**: Opentrons 20 uL Filter Tips </br>
**Slot 11**: Opentrons 200 uL Filter Tips </br>


---

### Protocol Steps
1. Set up - be sure to pre-cool the Temperature Module to 4 degrees C using settings in the OT app prior to running this protocol.
2. The protocol will alert the user to ensure reagents in sufficient volume are present on deck.
3. The p300 multi will use a single tip on the rear-most channel to deliver reaction buffer to the mix tube, then deliver enzyme mix to the mix tube, mix, and deliver the mixture (fragmentation mastermix) to the first column of the reagent plate.  
4. Using the first column of the reagent plate as source, the p20 multi will deliver fragmentation mastermix to each sample in the library prep plate.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
11bb6a
