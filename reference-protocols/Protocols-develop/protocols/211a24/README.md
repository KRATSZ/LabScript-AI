# Customizable Serial Dilution for OT-2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
    * Serial Dilution

## Description
This protocol allows for a customizable serial dilution workflow based on 4 text files containing worklist information. This protocol uses a P300 GEN2 single-channel pipette. The 4 steps, each corresponding to its own input text file, are as follows:
* diluent addition to serial dilution plate
* sample addition to serial dilution plate
* serial dilution across plate
* cherrypicking to load final plate

### Labware
* [NEST 96 Well Plate 100 µL PCR Full Skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 1 Well Reservoir 195 mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips?_gl=1*rt813e*_ga*MTg1MTY5ODQ4MC4xNjIwMzIwNjcz*_ga_GNSMNLW4RY*MTYyMjIyMzI1Ny40NC4xLjE2MjIyMjM1MjQuMA..&_ga=2.88970393.36901296.1622052353-1851698480.1620320673)

### Pipettes
* [Opentrons P300 Single-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549109789)

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
211a24
