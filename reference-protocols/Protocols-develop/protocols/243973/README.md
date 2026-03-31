# Protein Normalizaton with Email Notifications

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description
This protocol automates protein normalization with a CSV input. Additionally, it gives the user the ability to send and receive email notifications at points requiring user intervention.

Using the [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) and the [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette), diluents are added (based on volume) on up to seven plates with a single set of tips. After the diluents are added, the proteins are transferred with a new tip each time and again based on the volume outlined in the CSV.  

Before the OT-2 transfers the proteins, the robot will pause and prompt the user to add the plate containing proteins to the deck. If selected, the user will also receive an email when this step occurs. The same process will occur at the end of the protocol, letting the user know that they can remove the samples for downstream applications.

Explanation of complex parameters below:
* **P300-Multi Mount**: Select which mount the [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) is attached to.
* **P20-Multi Mount**: Select which mount the [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) is attached to.
* **Number of Destination Plates**: Specify the number of destination plates that are used in the protocol. Up to 7 plates can be used.
* **Transfer CSV**: Upload the CSV containing the information for normalization. The CSV should have a header row and the following columns (in this order): `Source Well`, `Destination Plate`, `Destination Well`, `Sample Volume`, `Diluent Volume`.
* **Email (if notifying)**: If receiving notifications via email, which email would you like to notify?
* **Email Password**: This is the password for the notification email (not your e-mail). The applications engineer that developed the protocol can supply this.

---

### Labware
* [Opentrons 20µL  Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)
* [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* Greiner Bio-One 96-Well Plate, \#650161

### Pipettes
* [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

### Reagents
* Diluent (PBST)

---

### Deck Setup
The deck should be setup as follows:</br>
**[Opentrons 20µL  Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)**: Slot 11</br>
**[Opentrons 300µL  Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)**: Slot 10</br>
**[NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)**: Slot 9</br>
**Protein Plate (Source)**: Slot 8, containing proteins</br>
**Destination Plate(s)**: Slots 1-7; plate numbers match slot numbers (Plate 1 in Slot 1, etc.)</br>

### Reagent Setup
The diluent (PBST) should be in A1 of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml).

---

### Protocol Steps
1. The [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will pick up a tip column and distribute diluent to all wells that require a volume greater than 20µL. The pipette will then drop the tip in the trash.
2. The [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will pick up a tip column and distribute diluent to all wells that require a volume equal to or less than 20µL. The pipette will then drop the tip in the trash.
3. The protocol will pause and prompt user to add the protein plate to the deck (slot 8). If emailing the user, the email will be sent at this point.
4. For each well/column requiring more than 20µL of sample, the [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will transfer the sample, using a new tip for each transfer, and mixing 4 times in the destination well.
5. For each well/column requiring 20µL or less of sample, the [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will transfer the sample, using a new tip for each transfer, and mixing 4 times in the destination well.
6. The protocol is complete. If receiving emails, the user will be notified via email at this point.


### Process
1. Input your protocol parameters above.
2. Download your protocol.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions), if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
243973
