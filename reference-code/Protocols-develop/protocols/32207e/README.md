# Diluting DNA with TE, Using .csv File

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps a 96 well plate with up to 96 samples of DNA, normalizing all DNA samples to the same concentration with TE. TE should not be filled more than 20mL in the 50mL falcon tube to prevent pipette plunging. One tip is used to load TE onto the plate, whereas one tip per sample is used for loading DNA samples to plate. After DNA is loaded, DNA and TE are mixed at 80% of the total well volume for 3 repetitions. If a volume greater than 180ul is passed in to the TE volume (greater than well volume), an error is thrown and the protocol will stop.  

Explanation of complex parameters below:
* `.csv file`: Please upload your csv file in the following format, header included (no commas in header!). "Name" column blocked out for proprietary reasons.
![csv file](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/32207e/Screen+Shot+2022-04-07+at+9.46.56+AM.png)
* `DNA Aspiration Rate`: Specify the rate at which to aspirate DNA. A value of 1 is default, 0.5 being 50% of the default value, 1.2 being 20% faster than the default value, etc.
* `Track tips?`: Specify whether to start at A1 of both tip racks, or to start picking up from where the last protocol left off.
* `P20/P300 Mount`: Specify which mount (left or right) to host the P20 and P300 single channel pipette.

---

### Labware
* [Opentrons 4-in-1 Tube Rack with 50mL Falcon Tubes](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Opentrons 300ul Tips](https://shop.opentrons.com/universal-filter-tips/)
* [Sarstedt PCR plate full skirt, 96 well, transparent, Low Profile, 100 µl](https://www.sarstedt.com/en/products/laboratory/pcr-molecular-biology/pcr-plates/product/72.1980/)

### Pipettes
* [Opentrons P20 Single Channel Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/32207e/Screen+Shot+2022-04-04+at+4.30.03+PM.png)

---

### Protocol Steps
1. This section should consist of a numerical outline of the protocol steps, somewhat analogous to the steps outlined by the user in their custom protocol submission.
2. example step: Samples are transferred from the source tuberacks on slots 1-2 to the PCR plate on slot 3, down columns and then across rows.
3. example step: Waste is removed from each sample on the magnetic module, ensuring the bead pellets are not contacted by the pipette tips.

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
32207e
