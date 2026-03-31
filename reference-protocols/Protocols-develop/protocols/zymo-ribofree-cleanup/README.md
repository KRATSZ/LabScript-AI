# Zymo-Seq RiboFree™ Total RNA Library Prep Select-a-Size MagBead Clean-up (robot 2)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	*	Zymo RiboFree™ Total RNA Library Prep

## Description
This protocol performs Select-a-Size MagBead Clean-up for the [Zymo-Seq RiboFree™ Total RNA Library Prep](https://files.zymoresearch.com/protocols/r3000_zymo-seq_ribofree_total_rna_library_kit.pdf). This protocol is meant to be run on a second OT-2 in conjunction with another OT-2 running the rest of the library prep (first strand cDNA synthesis, universal depletion, P7 and P5 adapter ligations, and library index PCR).

Samples will be processed down columns and then across rows (A1, B1, C1, ... A2, B2, etc.). Thoroughly mix reagent tubes thoroughly by flicking or pipetting before starting. Briefly spin down and load onto the temperature module according to `Setup` below.

The user is prompted to replace tipracks mid-protocol when necessary (for > 76 samples).

Links:
* [First Strand cDNA Synthesis and RiboFreeTM Universal Depletion (robot 1)](./zymo-ribofree-first-strand-cdna-synth-universal-depletion)
* [P7 Adapter Ligation (robot 1)](./zymo-ribofree-p7-adapter-ligation)
* [P5 Adapter Ligation (robot 1)](./zymo-ribofree-p5-adapter-ligation)
* [Library Index PCR (robot 1)](./zymo-ribofree-library-index-pcr)
* [Select-a-Size Magbead Clean-up (robot 2)](./zymo-ribofree-cleanup)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons Temperature Module GEN2](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Opentrons Magnetic Module GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) for [NEST 96-well PCR plate, full skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 12-channel reservoir 15ml](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [Opentrons P20 and P300 GEN2 multi-channel pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons 20µl and 50/300µl tipracks](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

12-channel reservoir (slot 2)  
![res setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/zymo-ribofree/cleanup_res.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the number of samples to process, the cleanup stage, and the respective mount sides for your P10 and P300 GEN1 multi-channel pipettes.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
zymo-ribofree
