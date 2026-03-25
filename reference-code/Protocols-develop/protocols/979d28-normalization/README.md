# Normalization

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
    * Normalization

## Description

Links:
<br></br>
[RNA Isolation](./979d28)
<br></br>
[Normalization](./979d28-normalization)
<br></br>
[qPCR Prep](./979d28-pcr)

This protocol performs a custom sample normalization and mastermix addition. You can find a template for file input [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/979d28-normalization/ex.csv).

---

### Modules
* [Temperature Module (GEN2) x2](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml)
* [VWR® PCR Plates, 96-Well 200ul #83007-374](https://us.vwr.com/store/product/36797606/vwr-pcr-plates-96-well) seated in [Opentrons 96-well aluminum block](https://shop.opentrons.com/aluminum-block-set/)
* [Eppendorf 1.5 mL Safe-Lock Snapcap](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Tubes-44515/Eppendorf-Safe-Lock-Tubes-PF-8863.html) seated in [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/979d28-normalization/deck.png)

### Reagent Setup

![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/979d28-normalization/reagents.png)

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
979d28
