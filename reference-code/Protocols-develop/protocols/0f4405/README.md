# NEBNext® Ultra™ II DNA Library Prep Kit for Illumina®

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* NEBNext® Ultra™ II DNA Library Prep Kit for Illumina®

## Description
This protocol performs the [NEBNext® Ultra™ II DNA Library Prep Kit for Illumina®](https://www.neb.com/products/e7645-nebnext-ultra-ii-dna-library-prep-kit-for-illumina#Protocols,%20Manuals%20&%20Usage). The protocol includes a fully automated End Repair PCR step on the Opentrons Thermocycler. Up to 24 samples can be processed in one protocol run without the need to replenish tipracks or change out labware.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Labware
* [Eppendorf twin.tec ® PCR Plate 96 #0030128648](https://www.eppendorf.com/de-de/eShop-Produkte/Spitzen-Reaktionsgef%C3%A4%C3%9Fe-und-Platten/Platten/Eppendorf-twintec-PCR-Plates-p-0030128648)
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [Opentrons 96-Well Aluminum Block](https://shop.opentrons.com/aluminum-block-set/)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/)

### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* [NEBNext® Ultra™ II DNA Library Prep Kit for Illumina®](https://www.neb.com/products/e7645-nebnext-ultra-ii-dna-library-prep-kit-for-illumina#Protocols,%20Manuals%20&%20Usage)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0f4405/deckv2.png)  

reservoir (slot 9):  
* column 1: EtOH
* column 2: elution buffer
* column 12: waste (loaded empty)

Thermocycler plate (slot 7, 8, 10, 11):  
* columns 1-3: DNA samples

Magnetic Module plate (slot 1):  
* columns 1-6: beads

Temperature Module plate (slot 3):
* column 1: mastermix 1
* column 2: adaptor
* column 3: mastermix 2
* column 4: USER
* columns 5-7: final PCR reagents

---

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0f4405
