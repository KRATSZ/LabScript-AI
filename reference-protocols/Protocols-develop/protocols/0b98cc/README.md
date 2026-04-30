# Viral Sample Titration

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Serial Dilution

## Description
This protocol performs viral titration (serial dilution) of viral samples. It adds media to the dilution plates and then begins the serial dilution process of up to 12 columns worth of samples. It will dilute the samples in one of four dilution plates and then add it to the analysis dish in a specific order (skipping 3 columns for every dilution).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons 200uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Corning 96 Well Round Bottom 1mL](https://ecatalog.corning.com/life-sciences/b2c/US/en/Genomics-&-Molecular-Biology/Automation-Consumables/Deep-Well-Plate/Corning%C2%AE-96-well-Polypropylene-Storage-Blocks/p/3958)
* [Corning 96-well Flat Clear Bottom Black Polystyrene TC-treated Microplate](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Black-Clear-and-White-Clear-Bottom-Polystyrene-Microplates/p/3603)
* [NEST 1 Well 195mL Reservoir](https://shop.opentrons.com/collections/reservoirs/products/nest-1-well-reservoir-195-ml)
* [P300 Multichannel GEN2](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Note:** The Dilution Plates utilize the Corning 96 Well Round Bottom 1mL and the Analysis Dishes utilize the Corning 96-well Flat Clear Bottom Black Polystyrene TC-treated Microplate.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0b98cc/0b98cc.png)

**Labware Type**
* Dilution Plate: Corning 96 Well Round Bottom 1mL
* Analysis Dish: Corning 96-well Flat Clear Bottom Black Polystyrene TC-treated Microplate
* Samples: NEST 96 Well Plate 100uL PCR Full Skirt
* Media Reservoir: NEST 1 Well 195mL Reservoir

**Protocol Steps**
1. Transfer appropriate volumes of media from the reservoir to each dilution plate on a per column basis using the multichannel pipette.
2. Sample from the first column (A1) is transferred to A1 of Dilution Plate 1 where it is mixed and then transffered to A1 on analysis dish 1.
3. Diluted sample is transferred from A1 of Dilution Plate 1 to A1 of Dilution Plate 2. It is thoroughly mixed and then transferred to A4 on Analysis Dish 1.
4. Diluted sample is transferred from A1 of Dilution Plate 2 to A1 of Dilution Plate 3. It is thoroughly mixed and then transferred to A7 on Analysis Dish 1.
5. Diluted sample is transferred from A1 of Dilution Plate 3 to A1 of Dilution Plate 4. It is thoroughly mixed and then transferred to A10 on Analysis Dish 1.
6. This completes one set of samples. This cycle will repeat for up to 12 columns worth of samples across four analysis dishes.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

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
0b98cc