# Omega Mag-Bind® Blood & Tissue DNA 96 Kit - 250μL Blood Protocol

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
    * Omega Mag-Bind® Blood & Tissue DNA 96 Kit

## Description
This is a flexible protocol accommodating the framework given for the 250µl Blood Protocol in the [Omega Mag-Bind® Blood & Tissue DNA 96 Kit](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-01-08/fl13zq3/Mag-Bind%C2%AE%20Blood%20%26%20Tissue%20DNA%20HDQ%2096%20Kit%20QMF27.0118.M6399%20v8.0.pdf),

Lysed samples should be loaded on the magnetic module in a NEST or USA Scientific 96-deepwell plate. For reagent layout in the 2 12-channel reservoirs used in this protocol, please see "Setup" below.

For sample traceability and consistency, samples are mapped directly from the magnetic extraction plate (magnetic module, slot 1) to the elution PCR plate (slot 5). Magnetic extraction plate well A1 is transferred to elution PCR plate A1, extraction plate well B1 to elution plate B1, ..., D2 to D2, etc.

Explanation of complex parameters below:
* `park tips`: If set to `yes` (recommended), the protocol will conserve tips between reagent addition and removal. Tips will be stored in the wells of an empty rack corresponding to the well of the sample that they access (tip parked in A1 of the empty rack will only be used for sample A1, tip parked in B1 only used for sample B1, etc.). If set to `no`, tips will always be used only once, and the user will be prompted to manually refill tipracks mid-protocol for high throughput runs.
* `track tips across protocol runs`: If set to `yes`, tip racks will be assumed to be in the same state that they were in the previous run. For example, if one completed protocol run accessed tips through column 5 of the 3rd tiprack, the next run will access tips starting at column 6 of the 3rd tiprack. If set to `no`, tips will be picked up from column 1 of the 1st tiprack.
* `flash`: If set to `yes`, the robot rail lights will flash during any automatic pauses in the protocol. If set to `no`, the lights will not flash.

---

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)  

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons magnetic module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml) or [USA Scientific 12 Well Reservoir 22 mL](https://labware.opentrons.com/usascientific_12_reservoir_22ml)
* [NEST 1 Well Reservoir 195 mL](https://labware.opentrons.com/nest_1_reservoir_195ml) or [Agilent 1 Well Reservoir 290 mL](https://www.agilent.com/store/en_US/Prod-201252-100/201252-100)
* [NEST 96 Well Plate 100 µL PCR Full Skirt](https://labware.opentrons.com/nest_96_wellplate_100ul_pcr_full_skirt) or [Bio-Rad 96 Well Plate 200 µL PCR](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [NEST 96 Deepwell Plate 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep) or [USA Scientific 96 Deep Well Plate 2.4 mL](https://labware.opentrons.com/usascientific_96_wellplate_2.4ml_deep)
* [Opentrons 96 Filter Tip Rack 200 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

* Reservoir 1: slot 2
* Reservoir 2: slot 3  
![reservoirs](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4fc750/Screen+Shot+2021-02-09+at+3.07.33+PM.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Select your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4fc750
