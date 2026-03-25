# Opentrons Heater Shaker Module Beta Test Protocol

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Heater Shaker
	* Heater Shaker Beta Test

## Description
This protocol performs beta-testing steps of the Opentrons Heater Shaker Module with user-determined parameters for selection of the target temperature of the heater shaker (37-95 degrees Celsius), the target shaking speed (recommended 200-2000 rpm although it is possible to go up to 3000 rpm), duration of time for shaking (minutes), n (dispense to every nth column of the heater shaker labware - to save run-time), the labware on the heater shaker (five options listed in the protocol parameters section of the python script), the source labware (a well plate or reservoir from the Opentrons Labware Library - see list in protocol parameters section of the python script), the destination labware (a well plate or reservoir from the Opentrons Labware Library - see list in protocol parameters section of the python script), the transfer volume, and the pipette to be used (any single- or multi-channel pipette). The beta-test protocol will open and close the heater shaker latch and report latch status to the log, set target temperature and proceed without waiting, report the current temperature to the log, report the selected target wells to the log, perform liquid transfers from the source labware to the heater shaker labware, wait to ensure the previously set temperature has been reached, start shaking and capture the start time, perform a pipette mix in the destination labware to demo a pipetting step NOT targeting the heater shaker but occurring during the timed shake, wait until the shake time has elapsed, stop shaking and report current rpm to the log, perform liquid transfer of 80 percent of the previously-dispensed volume from the heater shaker to the destination plate, deactivate the heater, open the latch, process complete.



---



### Labware
* Opentrons Tips for the Selected Pipette (https://shop.opentrons.com)
* Opentrons Heater Shaker Module-compatible labware (see five options in the protocol parameters section of the python script)
* Selected Source and Destination Labware ([see lists in the protocol parameters section of the python script] https://labware.opentrons.com/)


### Pipettes
* Selected single- or multi-channel Opentrons Gen2 Pipette - see list in the protocol parameters section of the python script (https://shop.opentrons.com)

### Reagents
Water for testing

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/heater-shaker-test/Screen+Shot+2022-06-21+at+12.15.17+PM.png)
</br>
</br>
**Slot 1**: Opentrons Heater Shaker Module with selected labware </br>
**Slot 3**: Source Labware (well plate or reservoir) </br>
**Slot 6**: Destination Labware (well plate or reservoir) </br>
**Slot 11**: Opentrons Tips


---

### Protocol Steps
1. The protocol will open and then close the heater shaker latch (latch status reported to the log).
2. The protocol will set the heater shaker target temperature and proceed without waiting (current temperature reported to the log).
3. The protocol will report the selected heater shaker wells (to be targeted for dispense) to the log (based on every_nth_column parameter).
4. Use the selected pipette to perform liquid transfers from the source labware to the heater shaker labware.
5. Wait to ensure reaching of the previously set heater shaker target temperature (current temperature reported to the log).
6. Start shaking (the protocol will capture the start time).
7. Use the selected pipette to perform pipette mixing in the destination labware (to test pipetting steps NOT targeting the heater shaker but occurring during the timed shake).
8. Wait until the shake time has elapsed.
9. Stop shaking (current rpm reported to the log).
10. Use the selected pipette to transfer 80 percent of the previously-dispensed liquid volume from the heater shaker to the destination labware.
11. Deactivate the heater (passive cooling).
12. Open the latch. Test process complete.


### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Ensure the OT App on your computer has been updated to version 6.1-beta.
3. Ensure the robot software on your OT-2 has been updated with the corresponding version.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
heater-shaker-test
