# Mass Spec Sample Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Mass Spec

## Description
This protocol performs mass spec sample prep on up to 96 samples using an Opentrons thermocycler for incubation steps. Samples should be specified as comma-separated values on the first line of a `.csv` file, as in the following example:
```
A1,B1,C1,D1,E1,G1,B2
```

The samples are filled according to the order of the `.csv`, and invalid wells are ignored (valid wells must be `A1`-`H12`)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [NEST 96-well PCR plate 100µL #402501](http://www.cell-nest.com/page94?_l=en&product_id=97&product_category=96) mounted in [Opentrons Thermocycler](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)
* [NEST 1.5ml snapcap microcentrifuge tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes) (or equivalent) mounted in [Opentrons 4-in-1 tuberack with 4x6 insert](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [Opentrons P20 GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 10/20ul tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Opentrons 4-in-1 tuberack with 4x6 1.5ml tube insert
* tube A1: enzyme
* tube B1: reagent 1
* tube C1: reagent 2

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Upload your `.csv` file containing wells to process, and input the mount side for your P50 single-channel pipette, and the incubation temperature (in degrees C).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
211fe1
