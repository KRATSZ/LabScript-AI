# Consolidation from .csv

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Consolidation

## Description
This protocol performs a sample consolidation from `.csv` file. The file should be organized in the following way **including header line**:

```
Plate Position,Source Well ID,Destination Tube ID,Volume,,
1,A1,A1,3.0,,
1,B1,A1,4.0,,
1,C1,B1,5.0,,
1,D1,A1,3.0,,
...
```

Empty lines are ignored. You can download a template file [here](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2020-03-07/b303m2c/Verogen-CP-Example-File.xlsx).

The destination tube for all sources will be a specified location (A1-D6) of the custom tuberack in slot 9.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Abgene 96-Well Microplates 330µl (ThermoFisher #AB0796)](https://www.thermofisher.com/order/catalog/product/AB0796#/AB0796)
* [Axygen™ 96-well PCR Microplates, barcoded 200µl #14-222-327](https://www.fishersci.com/shop/products/axygen-96-well-full-skirted-pcr-microplates-clear-sterilized/14222327)
* [Abgene™ 96 Well 2.2mL Polypropylene Deepwell Storage Plate](https://www.thermofisher.com/order/catalog/product/AB0661#/AB0661)
* [Opentrons P20 GEN2 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 20µl tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* VWR 5ml tubes seated in [Opentrons 3x5 tuberack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

![deck layout](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2020-03-07/8n13m3k/4507DEEA-59CD-4453-8825-E4AA78E421C9.jpeg)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the source plate type, P20 single-channel pipette mount, and transfer .csv file.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
09cdbe
