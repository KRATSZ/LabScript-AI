# Phytip Protein A, ProPlus, ProPlus LX Columns - Protein Purification

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Biotage](https://www.biotage.com/)



## Categories
* Protein Purification
	* Protein A, Pro Plus, Pro Plus LX Columns

## Description
This protocol (Protein Purification) performs protein purification by conducting dual flow chromatography using PhyTip® Protein A, ProPlus or
ProPlus LX Columns on the OT-2. It is developed to process up to 96 samples (a full 96-well plate).


Explanation of complex parameters below:
* `Number of Samples`: Specify number of samples (1-96) for this run.
* `P300 Multi-Channel Mount`: Specify which mount (left or right) to host the P300 Multi-Channel pipette.

---

### Labware
* [Thermo Fisher Nunc™ 96-Well Polypropylene Storage Microplates](https://www.thermofisher.com/order/catalog/product/249946?SID=srch-hj-249946)
* [Empty Opentrons 300µL Tip Rack for PhyTip® Columns](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

### Pipettes
* [P300 8-Channel GEN2](https://opentrons.com/pipettes/)

### Reagents
* [Biotage Protein A PhyTip® Columns](https://www.biotage.com/protein-a-phytip-column)
* [Biotage ProPlus PhyTip® Columns](https://www.biotage.com/proplus-phytip-column)
* [Biotage ProPlus LX PhyTip® Columns](https://www.biotage.com/proplus-phytip-column)
* Buffer kit provided by Biotage


---

### Deck Setup
* Slot 2 – 96-well V-bottom plate – Samples
* Slot 3 - PhyTip® Columns in an Opentrons 300µL Tipbox
* Slot 5 – 96-well V-bottom plate – 1st wash
* Slot 7 - 96-well V-bottom plate - 2nd wash
* Slot 9 - 96-well V-bottom plate - equilibration
* Slot 11 - 96-well V-bottom plate - elution

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-phytip-protein-puri/Screen+Shot+2022-06-13+at+3.54.11+PM.png)

### Reagent Setup
1. Prepare the sample plate (200 uL/well)
2. Fill the reagent plates with buffers according to the number of samples
to be processed.
a. Equilibration buffer – 200 uL per well
b. Wash buffer 1 – 200 uL per well
c. Wash buffer 2 – 200 uL per well
d. Elution buffer – 80 uL per well
3. Fill an Opentrons 300µL Tipbox with PhyTip® Columns according to the
number of samples to be processed.
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-phytip-protein-puri/Screen+Shot+2022-06-13+at+3.54.46+PM.png)
* For example: reagents and tips set for 72 samples (9 columns)

---

### Protocol Steps
1. Pick up PhyTip® Columns (slot 3).
2. Equilibrate – passing equilibration buffer (slot 9) over the resin bed for 4 cycles. In each cycle, the pipetting is programmed to aspirate and dispense 180 uL at 240 uL/min.
3. Capture – pass the sample (slot 2) over the resin bed for 8 cycles. In each cycle, the pipetting is programmed to aspirate and dispense 180 uL at 240 uL/min.
4. Wash – pass wash buffer 1 (slot 5) over the resin bed for 2 cycles. In each cycle, the pipetting is programmed to aspirate and dispense 180 uL at 480 uL/min.
5. Wash again – pass wash buffer 2 (slot 7) over the resin bed for 2
cycles. In each cycle, the pipetting is programmed to aspirate and
dispense 180 uL at 480 uL/min.
6. Elute - pass elution buffer (slot 11) over the resin bed for 4 cycles. In each cycle, the pipetting is programmed to aspirate and dispense 130 uL at 240 uL/min.


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
sci-phytip-protein-puri
