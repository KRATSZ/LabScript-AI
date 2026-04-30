# Normalization from .csv

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description
This protocol performs a custom sample normalization from a source PCR plate to a second PCR plate, diluting with water from a reservoir. Sample and diluent volumes are specified via .csv file in the following format, including the header line (empty lines ignored):

```
source plate well,destination plate well,volume sample (µl),volume diluent (µl)
A1, A1, 2, 28
```

You can download an example .csv to edit directly [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/ml-normalization/example_csv.csv).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Bio-Rad 96 Well Plate 200 µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [NEST 1-channel reservoir 195ml](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [Opentrons 10µl and 300µl tipracks](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons P10 and P300 GEN1 pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

NEST 1-channel reservoir (slot 1)
* channel 1: water for dilution

### Robot
* [OT-2](https://opentrons.com/ot-2)

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
8nhsa0-norm
