# Antibody Mastermix Creation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
	* Assay

## Description
This protocol performs custom mastermix creation from antibodies. The volumes of each antibody per sample to be transferred from a custom deepwell plate to the mastermix tube are specfied in a `.csv` input file, formatted as follows:

```
Volume per antibody(in ul),Antibody,Well
2.2,CD3 BUV395,A1
1.1,CD45 BUV496,A3
1.1,CD15 BUV563,A5
1.1,CD45RA BUV615,A7
2.2,CD14 BUV661,A9
0.55,CD8 BUV737,A11
2.2,CD11c BUV805,B2
1.1,CD25 BV421,B4
0.55,CD4 BV480,B6
2.2,CD16 BV605,B8
2.2,CD123 BV650,B10
2.2,CD127 BV711,B12
2.2,IgD BV750,C1
2.2,CD304 BV786,C3
2.2,CD141 BB515,C5
```

**Note that the headers line should be included, and empty lines are ignored.**

Links:
* [Flow Cytometry Staining](./53e6bc_flow_cytometry_staining)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [VWR 96-deepwell plate 2.2ml #10755-250](https://us.vwr.com/store/product/4693284/vwr-96-well-deep-well-plates)
* [VWR conical self-standing tubes 5ml #89497-740](https://us.vwr.com/store/product/11707931/self-standing-sample-tubes-5-and-10-ml-globe-scientific) (or equivalent) seated in [Opentrons 4-in-1 tuberack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 3x5 insert
* [VWR screwcap microcentrifuge tubes 1.5ml #](https://us.vwr.com/store/product/4674084/vwr-microcentrifuge-tubes-with-socket-screw-cap) (or equivalent) seated in [Opentrons 4-in-1 tuberack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 4x6 insert
* [Opentrons P300 GEN1 single-channel pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549109789)
* [Opentrons P10 GEN1 single-channel pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=31059478970462)
* [Opentrons 300ul tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 10ul tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

3x5 tuberack for 5ml screwcap tubes (slot 2)
* tube A1: mastermix (loaded empty)
* tube B1: PBS

4x6 tuberack for 1.5ml screwcap tubes (slot 4)
* tube A1: Brilliant Stain Buffer

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the respective mount sides for your P300 and P10 single-channel pipettes, the number of samples, and the antibody .csv file.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
53e6bc
