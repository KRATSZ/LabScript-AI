# Phytip Protein A, ProPlus, ProPlus LX Columns - Plate Prep

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Biotage](https://www.biotage.com/)



## Categories
* Protein Purification
	* Protein A, Pro Plus, Pro Plus LX Columns

## Description
This protocol (Plate Prep) performs pipetting to transfer reagents (equilibration buffer, wash buffer 1, wash buffer 2 and elution buffer) from a 12-well reagent stock reservoir to 96-well V-bottom plates (the reagent plates) on the OT-2. These reagent plates are used for the protein purification protocol of Phytip® Protein A, ProPlus or ProPlus LX Columns.

The protocol is developed to prepare sufficient reagents to process up to 96 samples (a full 96-well plate).

Explanation of complex parameters below:
* `Number of Samples`: Specify number of samples (1-96) for this run.
* `P300 Multi-Channel Mount`: Specify which mount (left or right) to host the P300 Multi-Channel pipette.


---

### Labware
* [Thermo Fisher Nunc™ 96-Well Polypropylene Storage Microplates](https://www.thermofisher.com/order/catalog/product/249946?SID=srch-hj-249946)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

### Pipettes
* [P300 8-Channel GEN2](https://opentrons.com/pipettes/)

### Reagents
* [Biotage Protein A PhyTip® Columns](https://www.biotage.com/protein-a-phytip-column)
* [Biotage ProPlus PhyTip® Columns](https://www.biotage.com/proplus-phytip-column)
* [Biotage ProPlus LX PhyTip® Columns](https://www.biotage.com/proplus-phytip-column)
* Buffer kit provided by Biotage


---

### Deck Setup
* Slot 5 – 96-well V-bottom plate – 1st wash
* Slot 6 - Tiprack1
* Slot 7 - 96-well V-bottom plate - 2nd wash
* Slot 8 – 12-well reagent stock reservoir
* Green – equilibration buffer (well 1 and well 2)
* Blue – wash buffer 1 (well 3 and well 4)
* Pink – wash buffer 2 (well 5 and well 6)
* Purple – elution buffer (well 7 and well 8)
* Slot 9 96-well V-bottom plate - equilibration
* Slot 11 - 96-well V-bottom plate - elution

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-phytip-protein-A/Screen+Shot+2022-06-08+at+2.50.25+PM.png)

### Reagent Setup
* Fill the reagent stock reservoir with buffers provided:
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-phytip-protein-A/Screen+Shot+2022-06-08+at+2.53.55+PM.png)

---

### Protocol Steps
1. Equilibration buffer from reagent stock reservoir (slot 8) is transferred to the “Equilibration” plate (slot 9) by the 8-channel pipette (200 uL per well).
2. Wash buffer 1 from reagent stock reservoir (slot 8) is transferred to the “1st wash” plate (slot 5) by the 8-channel pipette (200 uL per well).
3. Wash buffer 2 from reagent stock reservoir (slot 8) is transferred to the “2nd wash” plate (slot 7) by the 8-channel pipette (200 uL per well).
4. Elution buffer from reagent stock reservoir (slot 8) is transferred to the “Elution” plate (slot 11) by the 8-channel pipette (80 uL per well).


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
sci-phytip-protein-A
