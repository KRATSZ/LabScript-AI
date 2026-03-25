# Custom 384-Well Plate PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
    * PCR Prep

## Description

This protocol performs a custom PCR Prep from strip tubes seated in a custom cooling rack into a 384-well plate for up to 16 samples. The transfer scheme is follows:

![scheme](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/13ac78/Opentrons+Diagram+%233.jpeg)

---

### Labware
* [NEST PCR 8-Strip Tubes 0.2ml #403022](https://www.cell-nest.com/page94?_l=en&product_id=94) seated in [SSbio IsoFreeze PCR Rack #5650-T4](https://ssibio.com/product/5650-t4/)
* [ThermoFisher MicroAmp™ Optical 384-Well Reaction Plate #4343370](https://www.thermofisher.com/order/catalog/product/4343370?SID=srch-srp-4343370)
* [Opentrons 20uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

### Pipettes
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [P20 Single-Channel Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

### Reagents
* [ThermoFisher MagMax Viral/Pathogen Kit](https://www.thermofisher.com/order/catalog/product/A42356?SID=srch-srp-A42356)
* [ThermoFisher TaqMan Fast Advanced Master Mix](https://www.thermofisher.com/order/catalog/product/4444557?SID=srch-srp-4444557)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/13ac78/deck.png)

Reagents:
* green: mastermix
* blue: samples
* pink: positive control
* purple: molecular grade water

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
13ac78
