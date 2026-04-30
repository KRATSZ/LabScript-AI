# Swift Normalase Amplicon Panels (SNAP): Size Selection and Cleanup Part 2/2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
    * Swift Normalase Amplicon Panels (SNAP)

## Description

Links:
* [Part 1](./74841a)
* [Part 2](./74841a-2)

This is Part 2/2 of the Swift Normalase Amplicon Panels (SNAP) Size Selection and Cleanup protocol.

Explanation of complex parameters below:
* `park tips`: If set to `yes` (recommended), the protocol will conserve tips between reagent addition and removal. Tips will be stored in the wells of an empty rack corresponding to the well of the sample that they access (tip parked in A1 of the empty rack will only be used for sample A1, tip parked in B1 only used for sample B1, etc.). If set to `no`, tips will always be used only once, and the user will be prompted to manually refill tipracks mid-protocol for high throughput runs.
* `track tips across protocol runs`: If set to `yes`, tip racks will be assumed to be in the same state that they were in the previous run. For example, if one completed protocol run accessed tips through column 5 of the 3rd tiprack, the next run will access tips starting at column 6 of the 3rd tiprack. If set to `no`, tips will be picked up from column 1 of the 1st tiprack.
* `flash`: If set to `yes`, the robot rail lights will flash during any automatic pauses in the protocol. If set to `no`, the lights will not flash.

---

### Modules
* [Opentrons magnetic module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [USA Scientific 12 Well Reservoir 22 mL](https://labware.opentrons.com/usascientific_12_reservoir_22ml)
* [NEST 1 Well Reservoir 195 mL](https://labware.opentrons.com/nest_1_reservoir_195ml) or equivalent for waste
* [Bio-Rad 96 Well Plate 200 µL PCR Full Skirt](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Opentrons 96 Filter Tip Rack 200 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 96 Filter Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)

### Pipettes
* [Opentrons P300 8-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons P20 8-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

### Reagents
* [Swift Normalase Amplicon Panels (SNAP)](https://swiftbiosci.com/wp-content/uploads/2021/06/PRT-028-Swift-Normalase-Amplicon-Panel-SNAP-SARS-CoV-2-Panels-Rev-9-1.pdf)

---

### Deck Setup
![Setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/74841a/deck_setup.png)

### Reagent Setup
Reagent Reservoir (slot 5; volumes for 96-sample run):  
* channel 5: PEG, 3120µl
* channel 6: EtOH, 17280µl
* channel 7: EtOH, 17280µl
* channel 8: POST-PCR TE buffer, 1920µl

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
74841a
