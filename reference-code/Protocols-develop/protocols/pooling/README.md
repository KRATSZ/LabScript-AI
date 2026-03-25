# Pooling from .csv

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Pooling

## Description
This protocol performs a custom sample pooling from a source PCR plate to a 1.5, 2, or 5ml Eppendorf tube. Sample locations and volumes are specified via .csv file in the following format, including the header line (empty lines ignored):

```
source plate well,volume sample (µl)
A1, 28
C4, 12
```

The proper pipette for a given volume is automatically calculated. Tips are changed for each transfer.

You can download an example .csv to edit directly [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/pooling/ex.csv).

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)
* [HEPA Module](https://shop.opentrons.com/collections/hardware-modules/products/hepa-module)

### Labware
* [Eppendorf™ 96-Well twin.tec™ PCR Plate 250µl](https://www.fishersci.com/shop/products/eppendorf-96-well-twin-tec-pcr-plates-21/e951020389)
* [Opentrons 20µl and 300µl tipracks](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [Opentrons P20 and P300 GEN2 single-channel pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

---

### Deck Setup

![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/pooling/pooling.png)

---

## Process
1. Input the normalization .csv file, and the respective mount sides for your P10 and P50 GEN1 single-channel pipettes.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
pooling
