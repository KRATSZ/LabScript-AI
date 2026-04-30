# Chemical Denaturation with CSV Input

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps (3) 384 plates with urea, buffer and sample. One tip is used for each the urea and buffer reagents, with changing tips for the sample. Pipettes are selected dependent on the volume passed to the csv. If the protocol runs out of tips, it will pause and prompt the user to refill tip racks and resume. After sample is added, the well is mixed at 20ul for 3 repetitions.

Explanation of complex parameters below:
* `Number of 384 plates`: Specify how many 384 well plates there are for this run. Note that for plates less than 3, plates should be placed in order of slot number (1, 2, then 3), and csvs should also be uploaded in that order (from the top down below).
* `.CSV`: Find below the format for the urea/buffer, and sample csvs. NOTE: Always put an "x" in the top left well of the csv, and include the header line. All csvs should be seperate. For wells which receive no volume, input an "x" instead. Please see the csvs below for reference.

* Urea/buffer map:
![csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1fcf02/Screen+Shot+2022-03-08+at+2.09.38+PM.png)
* Sample map:
![csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1fcf02/Screen+Shot+2022-03-08+at+2.00.15+PM.png)

* `Urea/Buffer Initial Volume (mL)`: Specify the initial volume in mL in each the urea and buffer tubes.
* `P20/P300 Mount`: Specify which mount (left or right) to host the single-channel pipettes.


---

### Labware
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Greiner 384 Well Plate](https://shop.gbo.com/en/row/products/bioscience/microplates/384-well-microplates/384-well-polypropylene-microplates/781209.html)
* [Opentrons 20ul Tips](https://shop.opentrons.com/universal-filter-tips/?_gl=1*inwreh*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTY0Njc2NjI2OC43NjcuMS4xNjQ2NzY2OTQ5LjA.&_ga=2.148444917.339153637.1646060545-1365106149.1621361358)
* [Opentrons 300ul Tips](https://shop.opentrons.com/universal-filter-tips/?_gl=1*inwreh*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTY0Njc2NjI2OC43NjcuMS4xNjQ2NzY2OTQ5LjA.&_ga=2.148444917.339153637.1646060545-1365106149.1621361358)

### Pipettes
* [P20 Single-Channel Pipette](https://opentrons.com/pipettes/)
* [P300 Single-Channel Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1fcf02/Screen+Shot+2022-03-08+at+2.06.26+PM.png)


---

### Protocol Steps
1. Urea is added to plates 1, 2, and 3 in accordance to their respective csvs (one tip).
2. Buffer is added to plates 1, 2, and 3 in accordance to their respective csvs 5mm above the bottom of the well (one tip).
3. Sample is added to plates 1, 2, and 3 in accordance to their respective csvs with a mix step (change tips).

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
1fcf02
