# TG Nextera XT index kit v2 Set A to D

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Illumina Nextera XT

## Description 
This protocol automates the TG Nextera XT DNA Sample Preparation Kit from illumina on up to 96 samples. While this protocol functions perfectly fine on up to 96 samples, it will take a significant amount of time to run that many samples. For most preparations, there will need to be a technician available to replace tip boxes as they are used.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P300-multi channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 200ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons P20-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [Opentrons Thermocycler Module](https://shop.opentrons.com/products/thermocycler-module)
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/products/tempdeck)
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/products/magdeck)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Nextera XT DNA Library Preparation Kit](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-xt-dna.html)
* [Phusion High-Fidelity PCR Master Mix with HF Buffer](https://www.thermofisher.com/order/catalog/product/F531S#/F531S)
* [KAPA HiFi HotStart ReadyMix](https://rochesequencingstore.com/catalog/kapa-hifi-hotstart-readymix/)
* [Omega BioTek Mag-Bind TotalPure NGS](https://shop.opentrons.com/collections/verified-reagents/products/mag-bind-total-pure-ngs)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Load reagents into tempdeck. Phusion mastermix goes into well A1 and KAPA mastermix goes into well B1. The 8 north indexing primers go in A2,B2,C2,D2,A3,B3,C3,D3 and are used in that order (A2 -> row A, B2 -> row B). The 12 south indexing primers go in A4 to D6 and are used in that order (A4 -> column 1, B4 -> column 2). 
2. Load DNA plate. Only a single plate outside of the magnetic module or thermocycler module is used so that there is space for pipette tips. This plate gets switched out throughout the protocol. 
3. Load thermocycler plate. This plate will get reagent and DNA during the first automated steps of the protocol.
4. Load 12 column reservoir. This reservoir is used for H2O, magnetic beads, ethanol, and a location for trashing liquid. If running 96, you will need to make sure to fill up with nearly a full volume of ethanol. Beads go in the first column, H2O in the second column, and ethanol in the following 4 rows, depending on how many samples you are running. The final 6 columns are used as a liquid trash location.
5. Load pipette tips onto deck. Most of the time, users will have to replace the tips throughout the protocol.
6. Run the protocol
7. After reagents are loaded into the thermocycler plate, switch the DNA plate on the normal Opentrons deck with the primer plate. The plate will then be thermocycled in an initial PCR reaction.
8. After thermocycling, switch the thermocycler plate onto the magnetic module. Place an empty 96 well plate onto the thermocycler module and onto the blank Opentrons deck slot.
9. Another indexing reaction will occur with the samples in the thermocycler module. After that is completed, switch the thermocycler plate onto the magdeck (trashing the old magnetic module plate) and replace the blank Opentrons deck slot plate with an empty 96 well plate. This will be the output plate of the reaction. Continue the protocol.
10. After the protocol is complete, remove the microplate in slot 2. This plate is the output plate of the reaction.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
2e84cc
