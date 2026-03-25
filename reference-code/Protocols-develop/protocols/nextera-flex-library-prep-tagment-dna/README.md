# Nextera DNA Flex Library Prep: Tagment DNA

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Nextera DNA Flex Library Prep


## Description
This protocol performs the 'Tagment DNA' section of the [Nextera DNA Flex Library Prep protocol](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html).

Links:
* [Cherrypick Samples](./nextera-flex-library-prep-cherrypick-samples)
* [Tagment DNA](./nextera-flex-library-prep-tagment-dna)
* [Post Tagmentation Cleanup](./nextera-flex-library-prep-post-tag-cleanup)
* [Amplify Tagmented DNA](./nextera-flex-library-prep-amplify-tagmented-dna)
* [Cleanup Libraries](./nextera-flex-library-prep-cleanup-libraries)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Bio-Rad Hard Shell 96-well low profile PCR plate 200ul #hsp9601](bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Opentrons 4-in-1 tuberack with 1.5ml Eppendorf tubes](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* 200ul PCR strips
* [P50 Single/multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [300ul Opentrons tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Vortex BLT and TB1 vigorously for 10 seconds before placing in tube rack wells B1 and C1, respectively, and resuming. Preprogram the thermocycler according to the TAG program parameters described in the kit manual.

1.5ml Eppendorf Tuberack (slot 2)
* A1-B1: mastermix 1.5ml snapcap tubes (loaded empty, 1 tube needed per 48 samples)
* A2-B2: BLT in 0.5ml false-bottom tubes (1 tube needed per 48 samples)
* A3-B3: TB1 in 0.5ml false-bottom tubes (1 tube needed per 48 samples)

200ul PCR strips (slot 3 **only needed if using P50 multi-channel pipette**
* strip column 1: mastermix strip (loaded empty)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the mount side for your P50 single-channel pipette, whether you are using a P50 multi-channel pipette, the mount for your P50 multi-channel pipette (if applicable), and the number of samples to process.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).
