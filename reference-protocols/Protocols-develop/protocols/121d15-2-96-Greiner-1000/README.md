# Redo Replacement Picking (Greiner MASTERBLOCK 96 Well Plate 1000 µL)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking

## Description

Links:
* [Manual Cleave](./121d15)
<br />
<br />
* [Manual Cleave Elution (Off-deck Vacuum)](./121d15-4)
<br />
<br />
* [Manual Cleave, ACN + Elution (Off-deck Vacuum)](./121d15-5)
<br />
<br />
* [Manual Cleave, ACN + Elution (On-deck Vacuum)](./121d15-6)
<br />
<br />
* [HPLC Picking](./121d15-3)
<br />
<br />
* [Redo Replacement Picking (Greiner MASTERBLOCK 96 Well Plate 500 µL)](./121d15-2-96-Greiner-500)
<br />
<br />
* [Redo Replacement Picking (Greiner MASTERBLOCK 96 Well Plate 1000 µL)](./121d15-2-96-Greiner-1000)
<br />
<br />
* [Redo Replacement Picking (Irish Life Sciences 96 Well Plate 2200 µL)](./121d15-2-96-Irish-2200)
<br />
<br />
* [Redo Replacement Picking (Greiner Masterblock 384 Well Plate 225 µL)](./121d15-2-384)
<br />
<br />
* [Aliquoting - 2ml Tuberack to 2ml Tuberack](./121d15-7-2ml-2ml-aliquot)
<br />
<br />
* [Aliquoting - 15ml Tuberack to 2ml Tuberack](./121d15-7-2ml-15ml-aliquot)
<br />
<br />
* [Pooling - 2ml Tuberack to 2ml Tuberack](./121d15-7-2ml-2ml-pool)
<br />
<br />
* [Pooling - 2ml Tuberack to 15ml Tuberack](./121d15-7-2ml-15ml-pool)
<br />
<br />

This protocol performs a custom Redo Replacement Picking protocol from a worklist. The worklist should be specified as follows:

```
Number of Redo
8
pos TB_RCK_1,pos MTP_1,disposal_vol,transfer_vol
TUBE BAR,PLATE BAR
1,1,200,200
2,35,200,200
3,2,150,200
4,90,100,100
5,84
6,62
7,42
8,18
...
```

---

### Labware
* Custom 48-tuberack
* [Greiner MASTERBLOCK 96 Well Plate 500 µL](https://shop.gbo.com/en/row/products/bioscience/microplates/polypropylene-storage-plates/96-well-masterblock-0-5ml/786201.html)
* [Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

### Pipettes
* [P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/121d15/deck-greiner-1000.png)

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
121d15
