# Oxford Nanopore Technologies 16S Barcoding NGS Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Oxford Nanopore 16S Barcoding Kit

## Description

This protocol performs a semi-automated solution for the [Oxford Nanopore 16S Barcoding NGS Prep](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2022-02-22/yf03wql/16S%20Barcoding%20Kit%20SQK-RAB204-minion.pdf)

---

### Labware
* [Opentrons 4-in-1 Tube Rack Set](link to labware on shop.opentrons.com when applicable) with 4x6 insert for [1.5ml Eppendorf tubes](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Tubes-44515/Eppendorf-Safe-Lock-Tubes-PF-8863.html)
* [Applied Biosystems MicroAmp™ Optical 96-Well Reaction Plate #N8010560](https://www.thermofisher.com/order/catalog/product/N8010560) seated in [MicroAmp™ Splash-Free 96-Well Base #4312063](https://www.thermofisher.com/order/catalog/product/4312063)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/)

### Pipettes
* [P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

### Reagents
* [Oxford Nanopore Technologies16S Barcoding Kit #SQK-RAB204](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2022-02-22/yf03wql/16S%20Barcoding%20Kit%20SQK-RAB204-minion.pdf)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/277a3d/deck.png)  
* blue: water
* pink: longamp taq
* purple: barcodes
* green: starting samples
* orange: EtOH

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
277a3d
