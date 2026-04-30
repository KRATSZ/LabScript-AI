# Cherrypicking (Custom)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking


## Description
This protocol performs cherrypicking from x source plates to y destination plates, both Bio-Rad 96-well low profile PCR plates (200µl). The user can specify the sources and destinations in any slot, and the protocol will automatically load the plate in that slot. Tipracks will automatically be loaded in the remaining available slots. In the case that all tips are exhausted, the protocol pauses, and the user is prompted to refill the racks before resuming.

The CSV should be formatted like so:

```
source slot, source well, destination slot, destination well, volume
1,A1,3,A1,5
...
```

**The header line should be included (the first line from the .csv file is ignored)**

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Bio-Rad 96-well low profile PCR plates (200µl)](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Opentrons P50-single electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 300µl tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Upload CSV and input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Applications Engineering Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
8nhsa0
