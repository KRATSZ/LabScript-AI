# DNA Normalization from .csv

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description
This protocol performs a custom sample normalization from a source PCR plate to a second PCR plate and a third norm plate. Transfer take place from multiple locations specified below based on the volumes described in the example CSV below:

```
Plate LC (Source),Source Well #,ID ,concentration (ug/ml),yield (ug),Destination 1 volume (ul),Destination 1 (Dil),Destination 1 (Dil Plate) Well,concentration dil (ug/ml),yield (ug),Destination 2 volume (ul),Destination 2 (final norm plate),Destination 2 (well #)
LC 96-well plate,A1,pET4286,3000.00,6.00,10,LC Dil Plate,A1,300.00,6.00,20.00,Norm Plate,A1
LC 96-well plate,G3,pET4016,3000,6.00,10,LC Dil Plate,G3,300.00,6.00,20.00,Norm Plate,G3
LC 96-well plate,H3,pET4017,3300,6.00,10,LC Dil Plate,H3,330.00,6.00,18.18,Norm Plate,H3
HC 96-well plate,F3,pET4308,3000,6.00,10,HC Dil Plate,F3,300,6.00,20.00,Norm Plate,F3
HC 96-well plate,G3,pET4308,3000,6.00,10,HC Dil Plate,G3,300,6.00,20.00,Norm Plate,G3
HC 96-well plate,H3,pET4308,3000,6.00,10,HC Dil Plate,H3,300,6.00,20.00,Norm Plate,H3
water,F3,,,,,,,,,81.82,Norm Plate,F3
water,G3,,,,,,,,,80.00,Norm Plate,G3
water,H3,,,,,,,,,81.82,Norm Plate,H3
```

**Note: Save any .xlsx files as a .csv**

## Protocol Steps

1. Transfer 90 uL of Water to LC Dil Plate and HC Dil Plate 
2. Transfer necessary volumes of Water to Norm plate based on spreadsheet
3. Transfer DNA from LC Plates to LC Dil Plates
4. Transfer DNA from HC Plates to HC Dil Plates
5. Transfer DNA from LC Plate to Norm
6. Transfer DNA from LC Dil to Norm
7. Transfer DNA from HC Plate to Norm
8. Transfer DNA from HC Dil to Norm

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Agilent 1 Well Reservoir 290 mL](https://www.agilent.com/store/en_US/Prod-201252-100/201252-100)
* [Opentrons 20µl and 300µl tipracks](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons P20 and P300 GEN2 single-channel pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Thermo Scientific™ PCR Plate, 96-well, low profile, skirted](https://www.fishersci.se/shop/products/thermo-scientific-thermo-fast-96-well-full-skirted-plates-1/10039522)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons 300 uL Tip Rack (Slot 1, 2)
* Opentrons 20 uL Tip Rack (Slot 3, 4)
* LC 96-well plate (Slot 5)
* HC 96-well plate (Slot 6)
* Water (Slot 7)
* LC Dil Plate (Slot 8)
* HC Dil Plate (Slot 9)
* Norm Plate (Slot 10)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the DNA norm .csv file, and the respective mount sides for your P20 and P300 GEN2 single-channel pipettes.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
5654c0