# Peptide Mass Spec Sample Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Mass Spec

## Description
This protocol performs a custom mass spectrometry sample prep for peptides up to 48 samples.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [NEST 96-well PCR plate 100µl full skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons 20µl tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 300µl tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons P20 and P300 GEN2 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Deck Setup
* Nunc 96-well polystyrene V-bottom microwell plate (Slot 1)
* NEST 0.1 mL 96-Well PCR Plate, Full Skirt (Slot 2)
* NEST 12-well reservoir, 15 mL,Opentrons (Slot 3)
* Opentrons Magnetic Module GEN2 (Slot 4)
* Stellar Scientific Cluster Tubes Racked, 1.2 mL (Slot 4, On Magnetic Module)
* Opentrons 300 uL Tip Rack (Slot 5, Slot 8)
* Opentrons 20 uL Tip Rack (Slot 6, Slot 9)

NOTE: Switch the Cluster Tubes Plate with the NEST PCR Plate on the Magnetic Module once the Pause step is reached.

**Magnetic Module Engage Height from Well Bottom (mm)** refers to the height the magnet will move to from the bottom of the well. A value of 13.5 mm will move the tops of the magnets to level with that height value.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the mount side for your P20 and P300 multi-channel pipettes, the number of samples (max samples is 48), aspiration rate (this is the aspiration rate that is used when aspirating acetonitrile OR supernatant), and the volumes for the appropriate wash and supernatant transfer steps (in uL).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
701319
