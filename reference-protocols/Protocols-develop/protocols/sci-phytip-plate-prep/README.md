# Phytip Protein A, ProPlus, ProPlus LX Columns: Plate Prep


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Protein Purification
	* Protein A, Pro Plus, Pro Plus LX Columns


## Description
This protocol (Plate Prep) performs pipetting to transfer reagents (equilibration buffer, wash buffer 1, wash buffer 2 and elution buffer) from a 12-well reagent stock reservoir to 96-well V-bottom plates (the reagent plates) on the OT-2. These reagent plates are used for the protein purification protocol of Phytip® Protein A, ProPlus or ProPlus LX Columns.

The protocol is developed to prepare sufficient reagents to process up to 96 samples (a full 96-well plate).



### Labware
* Thermo Scientific 96 Well Plate V Bottom 450 uL #249944/249946
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons Fixed Trash


### Pipettes
* [Opentrons P300 8 Channel Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* Biotage Protein A PhyTip® Columns (https://www.biotage.com/protein-a-phytip-column)
* Biotage ProPlus PhyTip® Columns (https://www.biotage.com/proplus-phytip-column)
* Biotage ProPlus LX PhyTip® Columns (https://www.biotage.com/proplus-phytip-column)
* Buffer kit provided by Biotage



### Deck Setup
Slot 5 – 96-well V-bottom plate – 1st wash</br>
Slot 6 - Tiprack1</br>
Slot 7 - 96-well V-bottom plate - 2nd wash</br>
Slot 8 – 12-well reagent stock reservoir
* Green – equilibration buffer (well #1 and well #2)
* Blue – wash buffer 1 (well #3 and well #4)
* Pink – wash buffer 2 (well #5 and well #6)
* Purple – elution buffer (well #7 and well #8)

Slot 9 96-well V-bottom plate - equilibration</br>
Slot 11 - 96-well V-bottom plate - elution</br>
</br>
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-phytip-plate-prep/deck.jpg)


### Reagent Setup
Fill the reagent stock reservoir with buffers provided:</br>
</br>
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-phytip-plate-prep/reagents.png)


### Protocol Steps
1. Equilibration buffer from reagent stock reservoir (slot 8) is transferred to the “Equilibration” plate (slot 9) by the 8-channel pipet (200 uL per well)
2. Wash buffer 1 from reagent stock reservoir (slot 8) is transferred to the “1st wash” plate (slot 5) by the 8-channel pipet (200 uL per well)
3. Wash buffer 2 from reagent stock reservoir (slot 8) is transferred to the “2nd wash” plate (slot 7) by the 8-channel pipet (200 uL per well)
4. Elution buffer from reagent stock reservoir (slot 8) is transferred to the “Elution” plate (slot 11) by the 8-channel pipet (80 uL per well)


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
sci-phytip-plate-prep
