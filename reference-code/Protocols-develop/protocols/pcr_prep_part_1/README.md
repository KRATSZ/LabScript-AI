# OT-2 PCR Prep 1/2: Master Mix Assembly

### Author
[Opentrons (verified)](https://opentrons.com/)


## Categories
* PCR
    * Mastermix Assembly

## Description
Part 1 of 2: Master Mix Assembly

Links:
* [Part 1: Master Mix Assembly](./pcr_prep_part_1)
* [Part 2: Master Mix Distribution and DNA Transfer](./pcr_prep_part_2)

This protocol allows your robot to create a master mix solution using any reagents stored in one or two different types of tube racks, or reservoir well A2 to A12. The master mix will be created in well A1 of the trough. The ingredient information will be provided as a CSV file. See Additional Notes for more details.

Parameters:
* `right pipette type`: Which single channel pipette to use in the right mount
* `left pipette type`: Which single channel pipette to use in the left mount
* `Filter or regular tips`: Use filter tips or non-filtered.
* `Tuberack 1`: Tuberack 1 for reagents (optional)
* `Tuberack 2`: Tuberack 2 for reagents (optional)
* `12-well reservoir`: 12 well reservoir for mastermix target and optionally reagents in well A2-A12
* `master mix .csv file`: Input csv file (see format below)

---

### Labware
* [4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [12-well Trough](https://www.usascientific.com/12-channel-automation-reservoir.aspx)

### Pipettes
* [One or two single-Channel pipette(s)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

### Reagents
* Mastermix components, e.g. polymerase enzyme, buffer, dNTPs etc located in the tubes and reservoir well A2-A12 specified by your input csv file.

---

### Deck Setup
* Slot 1: Option of Opentrons tuberack/tube combo 1, or none
* Slot 2: Option of Opentrons tuberack/tube combo 2, or none
* Slot 3: Choice of Opentrons labware library 12-well reservoir
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/pcr_prep_part_1/deck.jpg)

### Reagent Setup
* Tuberack 1: slot 1 - any number of reagents that can fit on the tuberack (defined in the csv)
![tuberack 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/pcr_prep_part_1/tuberack1.jpg)
* Tuberack 2: slot 2 - any number of reagents that can fit on the tuberack (defined in the csv)
![tuberack 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/pcr_prep_part_1/tuberack2.jpg)

---

### Protocol Steps
1. The protocol reads a line from the csv and transfers that specific reagent from its tube or reservoir well to resevoir well A1 (i.e. the leftmost reservoir well).
2. The protocol repeats this until it has worked through the whole csv file.

## Process
1. Select your pipettes.
2. Select your labware
3. Upload your master mix CSV.
4. Download your protocol.
5. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
6. Set up your deck according to the deck map.
7. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
8. Hit "Run".
9. Robot will transfer each reagent from its source to well A1 of trough in slot 3.

### Additional Notes
Slot 1: Option of Opentrons tuberack/tube combo 1, or none
Slot 2: Option of Opentrons tuberack/tube combo 2, or none
Slot 3: 12-well Trough

Please reference our [Application Note](https://opentrons-protocol-library-website.s3.amazonaws.com/Technical+Notes/Thermocycler+PCR+Application+Note.pdf) for more information about the expected output of this protocol.

---

![csv_layout](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/1473-acies-bio/CSV.png)
* Slot 1 refers to tuberack 1 (slot 1) , slot 2 refers to tuberack 2 (slot 2) slot 3 refers to the reservoir

* The slot (1, 2, 3) and well (A1 - D6 for tubes, A2 to A12 for reservoir) describe source location of the reagent
* You can add as many reagents as necessary
* Make sure you do not reuse the same well in the same slot
* Keep the headers of the csv because the protocol expects them to be there.

---

If you have any questions about this protocol, please contact protocols@opentrons.com.

###### Internal
OT-2 PCR Prep v2
