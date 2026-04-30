# Omega Mag-Bind® Total RNA Isolation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
    * Omega Mag-Bind® Total RNA Isolation

## Description

Links:
<br></br>
[RNA Isolation](./979d28)
<br></br>
[Normalization](./979d28-normalization)
<br></br>
[qPCR Prep](./979d28-pcr)

This protocol performs the [Omega Mag-Bind® Total RNA 96 Kit](https://www.omegabiotek.com/product/total-cellular-rna-mag-bind-total-rna-96//?utm_source=google&utm_medium=ppc&utm_campaign=128157293756&utm_term=total%20rna%20extraction%20kit&utm_content=b&gclid=Cj0KCQjw-daUBhCIARIsALbkjSb5Gx-Bz7K1R_Dw_ePhpzhX8NNtwe_9GP1LXR7SfOaeOHWgEnehFE4aAtRVEALw_wcB) protocol.

Samples should be loaded on the magnetic module in a NEST deepwell plate. For reagent layout in the 2 12-channel reservoirs used in this protocol, please see "Setup" below.

There are several user-intervention steps to move the deepwell isolation plate to and from the Magnetic Module and QInstruments Bioshake.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [QInstruments BioShake 3000](https://www.qinstruments.com/automation/bioshake-3000/) with adapter for OT-2

### Labware
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml)
* [NEST 1 Well Reservoir 195 mL](https://labware.opentrons.com/nest_1_reservoir_195ml)
* [NEST 96 Well Plate 100 µL PCR Full Skirt](https://labware.opentrons.com/nest_96_wellplate_100ul_pcr_full_skirt)
* [NEST 96 Deepwell Plate 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep)
* [VWR® PCR Plates, 96-Well 200ul #83007-374](https://us.vwr.com/store/product/36797606/vwr-pcr-plates-96-well) seated in [Opentrons 96-well aluminum block](https://shop.opentrons.com/aluminum-block-set/)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)

### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* [Omega Mag-Bind® Total RNA 96 Kit](https://www.omegabiotek.com/product/total-cellular-rna-mag-bind-total-rna-96//?utm_source=google&utm_medium=ppc&utm_campaign=128157293756&utm_term=total%20rna%20extraction%20kit&utm_content=b&gclid=Cj0KCQjw-daUBhCIARIsALbkjSb5Gx-Bz7K1R_Dw_ePhpzhX8NNtwe_9GP1LXR7SfOaeOHWgEnehFE4aAtRVEALw_wcB)

---

### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/979d28/deck.png)

### Reagent Setup

All volumes for 48-sample throughput

![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/979d28/reagents.png)

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
