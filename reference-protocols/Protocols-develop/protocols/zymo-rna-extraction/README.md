# Zymo Quick-DNA/RNA Viral MagBead Extraction

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Covid Workstation
	* RNA Extraction


## Description
This protocol automates the [Zymo Quick-DNA/RNA Viral MagBead Extraction Kit](https://www.zymoresearch.com/collections/quick-dna-rna-viral-kits/products/quick-dna-rna-viral-magbead). This kit is designed for high-throughput purification of viral DNA and/or RNA and the isolated nucleic acids are ready for all downstream applications, such as RT-qPCR, Next-Gen Sequencing, and many others.<br/>
<br/>
This kit can be used for Station B (RNA extraction) as part of our [COVID Workstation](https://blog.opentrons.com/how-to-use-opentrons-to-test-for-covid-19/).



---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase consumables, labware, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.16.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons Temperature Module with 96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons P300 8-Channel Pipette, Gen 2](https://opentrons.com/pipettes/)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 4-in-1 Tube Rack with 24-Well Top](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [NEST 1.5mL Microcentrifuge Tubes](https://shop.opentrons.com/collections/tubes/products/nest-microcentrifuge-tubes)
* [NEST 96-Deepwell Plate, 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [NEST 1-Well Reservoir, 195mL](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir)
* [Zymo Quick-DNA/RNA Viral MagBead Kit](https://www.zymoresearch.com/collections/quick-dna-rna-viral-kits/products/quick-dna-rna-viral-magbead)
* Ethanol, 95-100%
* Sample, 400µL per well


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Note - Before running this protocol, make sure you clean the OT-2. For more information on cleaning the OT-2, check out [this guide](https://support.opentrons.com/en/articles/1795522-cleaning-your-ot-2).<br/>
<br/>
The setup for this protocol varies slightly, depending on the number of samples the user selects.<br/>
<br/>
**Labware Setup**<br/>
<br/>
Slot 2: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml) with reagents (see below)<br/>
<br/>
Slot 3: [Opentrons Temperature Module with 96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with clean and empty [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)<br/>
<br/>
Slot 4: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [NEST 96-Deepwell Plate, 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate), containing samples*<br/>
*Samples should be loaded in odd-numbered columns only*<br/>
<br/>
Slot 5: [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)<br/>
<br/>
Slot 8: [Opentrons 4-in-1 Tube Rack with 24-Well Top](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1), containing reagents in [NEST 1.5mL Microcentrifuge Tubes](https://shop.opentrons.com/collections/tubes/products/nest-microcentrifuge-tubes) (see below)<br/>
<br/>
[Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)<br/>
* if 8 samples, Slot 1
* if 16 samples, Slots 1 and 6
* if 24 samples, Slots 1, 6, and 9
* if 32 samples, Slots 1, 6, 7, and 9
* if 40 or 48 samples, Slots 1, 6, 7, 9, and 10

<br/>
<br/>
**Reagent Setup**<br/>
<br/>
[Opentrons 4-in-1 Tube Rack with 24-Well Top](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)<br/>
D1: *Proteinase K*, 4µL per sample<br/>
D6: *Extraction Control Spike-In*, if using<br/>
<br/>
[NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)<br/>
For every 8 samples, the following reagents are needed:
* 7mL Zymo Viral DNA/RNA Buffer + 350µL of Zymo MagBeads
* 4.5mL of Zymo Wash Buffer 1
* 4.5mL of Zymo Wash Buffer 2
* 4.5mL of Ethanol (Ethanol Wash 1)
* 4.5mL Ethanol (Ethanol Wash 2)

<br/>

Slot 1: Zymo Viral DNA/RNA Buffer + Zymo MagBeads, 8/16 samples<br/>
Slot 2: Zymo Viral DNA/RNA Buffer + Zymo MagBeads, 24/32 samples<br/>
Slot 3: Zymo Viral DNA/RNA Buffer + Zymo MagBeads, 40/48 samples<br/>
Slot 4: Zymo Wash Buffer 1, 8/16/24 samples<br/>
Slot 5: Zymo Wash Buffer 1, 32/40/48 samples<br/>
Slot 6: Zymo Wash Buffer 2, 8/16/24 samples<br/>
Slot 7: Zymo Wash Buffer 2, 32/40/48 samples<br/>
Slot 8: Ethanol (Ethanol Wash 1), 8/16/24 samples<br/>
Slot 9: Ethanol (Ethanol Wash 1), 32/40/48 samples<br/>
Slot 10: Ethanol (Ethanol Wash 2), 8/16/24 samples<br/>
Slot 11: Ethanol (Ethanol Wash 2), 32/40/48 samples<br/>
Slot 12: Nuclease-Free Water, 3.5-4mL<br/>
<br/>
**Full Deck Layout:**
![Deck Layout](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/zymo-rna-extraction/zymo_48_layout.png)



__Using the customizations fields, below set up your protocol.__
* **Number of Samples**: Specify the number of samples you'd like to run.
* **Amount of Spike-in**: Specify how much control RNA (or other spike-in) should be added to each well. If not using a spike-in, leave as 0.
* **Return tips after wash step**: Specify whether to drop tips into trash bin after use, or to replace in tip rack for easy disposal.





### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
zymo-rna-extraction
