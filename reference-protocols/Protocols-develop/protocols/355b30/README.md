# Sample Mixing From CSV

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Pooling

## Description
This protocol uses single-channel pipettes to prepare a number of sample mixtures composed of a number of samples from a number of sample groups according to an input CSV file. User-determined parameters are available for selection of the left and right pipettes (none, p20 single, p300 single or p1000), pipetting mode (one pipette operating alone, two pipettes operating independently with all steps of one transfer being completed before any steps of the next transfer are started, or two pipettes multi-tasking with coordinated tip pickups, aspirations, dispenses, and tip drops), source and destination labware (see dropdown lists below), flow rates, and filtered or standard pipette tips. The pipette used for each transfer will be one with a volume range inclusive of the transfer volume (p20 for transfer volume 1-20 uL, p300 for 20-200 uL, p1000 for 100 - 1000 uL) or the next smaller pipette if the former is not available. If pipettes are selected that are not compatible with the volumes specified (10 uL transfer volume with p300 and p1000 pipettes for example), an error will be thrown to notify the user prior to the start of the OT-2 run. If the aspiration volume + air gap volume exceeds tip capacity the transfer will be divided into multiple transfers having equal volume.

Links:
* [example input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/355b30/csv_example.csv)

![screenshot input csv file](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/355b30/screenshot-input_csv.png)

---



### Labware
* Opentrons Tips for the Selected Pipette (https://shop.opentrons.com)
* Opentrons Temperature Modules (https://shop.opentrons.com/modules/)
* Selected Source and Destination Labware ([see parameter dropdown lists below] https://labware.opentrons.com/)


### Pipettes
* Selected single-channel Opentrons Gen2 Pipettes - see dropdown lists below (https://shop.opentrons.com)

### Reagents
Samples in Sample Groups

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/355b30/screenshot-deck.png)
</br>
</br>
**Slot 1**: Opentrons Temperature Module with dropdown-selected labware </br>
**Slot 4**: 2nd Opentrons Temperature Module with dropdown-selected labware </br>
**Slots 2-6,11**: dropdown-selected labware </br>
**Slots 7-9**: Opentrons Tips </br>
**Slot 10**: dropdown-selected reservoir </br>


---

### Protocol Steps
1. The protocol will obtain source and destination locations and transfer volume from the input csv file.
2. Using the selected single-channel pipettes (1 or 2, same or different), transfer samples to final sample tubes as specified in the input csv file. Include an air gap after aspiration. Include a blow out and tip touch after dispense.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
355b30
