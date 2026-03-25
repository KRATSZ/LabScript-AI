# Amplex Red Hydrogen Peroxide Assay

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Standard curve for Hydrogen Peroxide
	* Measurement of peroxides/hydrogen peroxide from THP-1 cells

## Description
This protocol can be used to measure the levels of hydrogen peroxide from THP-1 cells using Amplex Red reagent kit on the OT-2. 96-well plate format is used for this protocol.

Explanation of complex parameters below:
* `Number of Samples (5-12)`: Specify the number of samples for this run (from 5 to 12 samples).
* `P300/P20 Mount`: Specify which mount (left or right) for the P300 and P20 single channel pipettes.  

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)
* [HEPA Module](https://shop.opentrons.com/collections/hardware-modules/products/hepa-module)

### Labware
* Greiner-Bio One 96-Well White TC plate with clear bottom

* [Opentrons 96 Filter Tip rack 200μL](https://shop.opentrons.com/universal-filter-tips/)

* [Opentrons 96 Filter Tip rack 20μL](https://shop.opentrons.com/universal-filter-tips/)

* [Opentrons 10 Tube Rack with Falcon 4X50 mL, 6X15mL Conical](https://shop.opentrons.com/consumables/)

* [(2) Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://shop.opentrons.com/consumables/)


### Pipettes
* [P300 Single GEN2 pipette](https://opentrons.com/pipettes/)
* [P20 Single GEN2 pipette](https://opentrons.com/pipettes/)

### Reagents
* [Amplex Red Reagent Kit Cat No. A22188](https://www.thermofisher.com/order/catalog/product/A22188)
* [THP-1 Macrophage-like cells (ATCC, Manassas, VA, USA) (No.TIB-202)](https://www.atcc.org/products/tib-202)
* [Phenol Red Free RPMI 1640 medium (Thermofisher Scientific 11835030)](https://www.thermofisher.com/order/catalog/product/11835030)
* [Phorbol 12-myristate 13-acetate (PMA) (Sigma Aldrich P1585-1MG)](https://www.sigmaaldrich.com/US/en/product/sigma/p1585)
* [Fetal Bovine Serum (FBS) Not Heat Inactivated (ATCC, Cat No. 30-2020)](https://www.atcc.org/products/30-2020)


---

### Deck Setup
* Slot 3 Temperature Module- Plate initially at 23°C(deactivated) and after reagent addition, target temperature is 37° C.
* Slot 4 Opentrons 96 Filter Tip rack 200μl
* Slot 5 Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap- PMA Dilutions from 10mM to 10μM.
* Slot 7 Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap- Concentrations of H2O2 for standard curve (0.1, 0.2, 0.3, 0.4, 0.5, 1 and 2 μM) and concentrations of PMA from 0-150 ng/mL
* Slot 10 Opentrons 96 Filter Tip rack 20μl
* Slot 11 Opentrons 10 Tube Rack with Falcon 4X50 mL, 6X15mL Conical-Rack for holding 5X Reaction buffer, 1X Reaction buffer and Amplex Red Working Reagent

![figure1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-amplex-red/figure1.png)

* Figure 1 Deck layout after the reagent additions is carried out.
Slot 9 A1 tube contains (5X reaction buffer)
A3 falcon tube contains Distilled water for the 5X reaction buffer dilution. After addition of 5X to the tube, results in 1X Reaction Buffer being present in the same
B1 contains empty tube in which 1X Reaction buffer, Amplex red dye and HRP are dispensed during the protocol run.
Slot 7 Opentrons 24 tube rack Eppendorfs A1 to A6 has 20mM,0.0μM, 0.1μM,0.2μM, 0.3μM, 0.4μM concentrations of H2O2
Eppendorfs B1 to B6 has 0.5μM,1μM 2μM, 1mM, 100μM and 20μM of H2O2
Eppendorfs C1 to D1 have PMA concentrations of 0,10,25,50,75,100 and 150 ng/mL
respectively.
Eppendorfs D3, D4 and D5 have reagents 3% H2O2, HRP (Horse Radish Peroxidase) and Amplex red dye respectively
Slot 5 Opentrons 24 tube rack Eppendorfs from A1 to A3 have PMA concentrations of 1mM,100μM and 10μM respectively.
Slot3 The 96 well plate on the temperature module has the layout where Rows 0 and 2 have different concentrations of H2O2 standards ranging from 0 to 2μM added to wells (50μl). The rows 4 to 6 (columns 1 to 7; E1, F1 and G1 have cells which are untreated followed by E2, F2, G2 having cells treated with 10ng/mL of PMA till E7, F7 and G7 being cells treated with 150ng/mL of PMA (50μl)

![figure2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-amplex-red/figure2.png)

* Figure 2 Deck Layout after addition of Amplex red reagent to the 96-well plate that sits on the temperature module (Slot 3).

![figure3](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-amplex-red/figure3.png)

* Figure 3 This representation shows the addition of 50μl of Amplex red working solution to the Blank wells A1 and A2 (Figure shows first well A1 containing 1X Reaction Buffer, to which the Amplex red working solution is added). Same steps are followed for the H2O2 standards (Figure shows representative well A9 displaying the addition of Amplex red). Likewise, the steps are same for wells in which THP-1 cells are present and contain different concentrations of PMA (one representative well, E6 is shown above)

---

### Protocol Steps
1. The reagents that are kept in different deck slots are 5X Reaction buffer, distilled water,3%H2O2, HRP, Amplex Red and 1mM PMA.
2. Pick up 200μL tips from Slot 4. Dilution of reaction buffer from 5X to 1X concentration with distilled water
3. Dilution of the H2O2 stock from 3% (provided in the kit), to a required working concentration of 20mM, followed by dilution for the standard H2O2 concentrations ranging from 0-2μM in Eppendorf rack kept in Slot 7.
4. Dilution of PMA concentrations from 10mM to 10μM in Slot 5.
5. Dilution of PMA further, ranging from 0 to 150ng/mL in 1X Reaction buffer in Slot 7
6. Preparation of the working Amplex red-reaction buffer-HRP reagent in Slot 11. It is stored away in dark after preparation to avoid any loss of fluorescence. till the final step (put back in B1 slot of Opentrons 10-Tube Rack) when the reagent is added to the wells)
7. Concentrations of H2O2 for the standard curve (0 to 2μM) (Rows 0 and 2 of the 96 well plate that is kept on Temperature deck) were dispensed using 200μL tips.
8. Removal of complete medium from the wells of 96 well plate that contains cells (manual step) (E1 to E7, F1 to F7 and G1 to G7).
9. Putting the 96 well plate back to the temperature deck and maintained at 23°C for addition of different concentrations of PMA(0-150ng/mL)
10. Finally, the working reagent kept in the dark is taken out and placed in respective location in the Opentrons 10-Tube Rack (Location B1). 50μL of working reagent is dispensed in wells containing standards and THP-1 cells.
11. The temperature deck is set to 37°C. The fluorescence readings are taken at 15, 30, 45 and 60 min duration in the Biotek H1 instrument with excitation at 530 nm and emission at 590nm.

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
Amplex Red Hydrogen Peroxide Assay
