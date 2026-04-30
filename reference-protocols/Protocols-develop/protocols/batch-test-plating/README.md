# Batch Test Plating

### Author
[Innovative Solutions - Argenitna]

### Partner
[Facundo Rodriguez Goren]



## Categories
* PCR
    * PCR Prep


## Description
This is a flexible protocol that helps you to prepare the PCR plate for a batch test of 12 samples and 2 No Template Controls, with the previous adition of the Master Mix
The protocol is broken down into 3 main parts:
* Mix dispensing
* Samples Dispensing
* NTC dispensing


---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)


### Labware
* [nest_96_wellplate_100ul_pcr_full_skirt](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* [opentrons_96_filtertiprack_20ul](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* [opentrons_24_tuberack_generic_2ml_screwcap](https://shop.opentrons.com/4-in-1-tube-rack-set/)



### Pipettes
* [p20_single_gen2](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)




---

### Protocol Steps
1. Master Mix dispensing from Temperature Module to pcr plate
2. Samples dispensing from Tuberack to pcr plate
3. NTC dispensing from Tuberack to pcr plate

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.


###### Internal
batch-test-plating
