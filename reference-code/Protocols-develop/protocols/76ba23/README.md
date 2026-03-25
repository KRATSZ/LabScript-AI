# NGS Library Prep for Targeted Sequencing of DNA Methylation Patterns in Cell-Free DNA: Step 1 of 5: DNA Extraction

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * Zymoresearch: EZ DNA Methylation-Gold Kit

## Description
Part 1 of 5: Extraction and clean-up of cell-free DNA from 96 plasma or saliva patient specimens.

Links:
* [Part 1: DNA Extraction](http://protocols.opentrons.com/protocol/76ba23)
* [Part 2: Bisulfite Conversion](http://protocols.opentrons.com/protocol/76ba23-bisulfite_conversion)
* [Part 3: PCR1](http://protocols.opentrons.com/protocol/76ba23-pcr1)
* [Part 4: PCR2](http://protocols.opentrons.com/protocol/76ba23-pcr2)
* [Part 5: Pooling](http://protocols.opentrons.com/protocol/76ba23-pooling)

With this protocol, your robot will use reagents from the Zymoresearch EZ DNA Methylation-Gold Kit [Zymoresearch EZ DNA Methylation-Gold Kit](https://www.zymoresearch.com/collections/ez-dna-methylation-gold-kits) to perform the custom steps (DNA extraction, Bisulfite Conversion, PCR1, PCR2, Pooling) detailed in the HKG SOP.[HKG SOP](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-03-04/vw23kchHKG%20Standard%20Operating%20Procedure%20for%20DNA%20extraction%20Targeted%20next%20generation%20sequencing%20and%20.xlsx).

This is part 1 of the protocol: DNA Extraction.

This step performs the extraction and bead-clean up of 96 patient samples (plasma or saliva) listed in the sample manifest and follows the HKG SOP described above. A current sample manifest can be uploaded and integrated into this protocol by using the "Uploaded CSV Copy of Sample Manifest" parameter below. The OT-2 will read the sample type and sample volume from the uploaded manifest and then set up and perform the experimental steps accordingly.

After the steps carried out in this protocol (part 1), proceed with part 2: Bisulfite Conversion.


## Protocol Steps

Set up: Place patient samples, bead premix, DNA extraction plate (with duplicate if sample volume >= 1 mL), magnetic module, waste reservoir, elution plate and tips on the OT-2 deck.  

The OT-2 will perform the following steps:
1. Distribute premix and sample to the DNA extraction plates.
2. Pause for manual steps (OT-2 deck lights will signal pauses):

           Seal the plates.
           Invert the plates 10 times to mix sample and premix.
           Shake plates vigorously for 10 minutes on plate shaker.
           Spin the plates.

           Unseal the primary dna extraction plate and place it on
           the OT-2 magnetic module. If there is a duplicate plate,
           unseal and place it back in its original OT-2 deck slot.

           Remove the empty premix reservoir from the OT-2 deck.
           Replace it with HKG DNA Wash Buffer 1 reservoir.

           Remove the sample plate from the OT-2 deck. Replace it
           with a deep well plate containing water (in column 1)
           for the elution step.

           Additional pauses for wash, ethanol, waste or tip replenishment.

3. Remove bead supernatants, combine beads from DNA extraction plate and duplicate plate, wash beads, elute and transfer eluate to fresh PCR plate.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons Magnetic Module (Deck Slot 4)
* Opentrons p300 tips (Deck Slots 6 and 9)
* 96 patient samples ("usascientific_96_wellplate_2.4ml_deep" Deck slot 1)
* DNA extraction plate ("usascientific_96_wellplate_2.4ml_deep" Deck slot 2)
* (if sample volume >= 1 mL) duplicate DNA extraction plate (Deck slot 5)
* reservoir for bead premix, wash, ethanol ("nest_1_reservoir_195ml" Deck slot 3)
* pcr plate for eluate ("nest_96_wellplate_100ul_pcr_full_skirt" Deck slot 10)
* reservoir for waste ("nest_1_reservoir_195ml" Deck slot 11)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Minutes to Air Dry Beads", "Choose Filtered or Standard Tips for P300 multi", and "Uploaded CSV Copy of Sample Manifest" parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
76ba23
