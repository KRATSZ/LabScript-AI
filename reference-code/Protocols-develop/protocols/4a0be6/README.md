# Tube Filling Sarstedt Tubes in Custom 12-, 24-, or 48-Tube Racks

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Tube Filling

## Description
This protocol is an updated version (APIv1 to APIv2) of this protocol: [Tube Filling into 48-well or 24-well Tube Racks](https://protocol-delivery.protocols.opentrons.com/protocol/4a0be6)

This protocol allows your robot to transfer solution from a single source tube (15 mL or 50 mL Falcon conical tube) or Beckman Coulter reservoir to up to nine 48-well, 24-well, or 12-well tube racks containing Sarstedt screw-cap tubes (either 0.5 mL, 1.5 mL or 2 mL). User must specify parameters (explained below) for each run.


Explanation of complex parameters below:
* **Transfer Volume (in µL)**: volume to be transferred to each Sarstedt tube
* **Tube Rack Type**: tube rack format to be used to hold the Sarstedt tubes
* **Tube Type**: Sarstedt tube format to be used in the protocol
* **Number of Racks**: total number of Sarstedt tube racks to be filled (1-9)
* **Source Container Type**: Labware containing reagent to be distributed
* **Starting Stock Volume (in mL)**: starting volume inside source container
* **Pipette Type**: Single-channel Pipette to be used
* **Pipette Mount**: the side to which you wish to attach the above pipette
* **Starting Tip**: the tip to be used in the tip rack, pick from A1-H12
* **Dispense Mode**: choose to either *transfer* (1-to-1) or *distribute* (1-to-many)
* **Touch Tip?**: this will add an additional touch tip after dispensing liquid


---

### Labware
* [Opentrons Tiprack](https://shop.opentrons.com/collections/opentrons-tips)
* Source Labware:</br>
15mL Falcon Tube in [Opentrons Tube Rack with 15 Tube Topper](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1),</br>
50mL Falcon Tube in [Opentrons Tube Rack with 6 Tube Topper](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1),</br>
or Beckman Coulter Reservoir</br>
* Custom Tube Rack with Sarstedt Tubes

### Pipettes
* [Opentrons Single-Channel Pipette (GEN1 or GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

---

### Deck Setup
**Slot 1**: Source Labware containing reagent</br>
**Slots 2-10**: Custom Tube Racks containing Sarstedt Tubes</br>
**Slot 11**: [Opentrons Tiprack](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>


### Reagent Setup
The amount of reagent should be noted and added as a parameter. Reagent will go into 15mL or 50mL Falcon tube and placed in A1 of tube rack. Additionally, reagent can be placed in Beckman Coulter Reservoir.

---

### Protocol Steps
1. Pipette will pick up tip (from specified location).
2. Pipette will transfer/distribute **Transfer Volume** from **Source Labware** to all tubes in first rack (slot 2).
3. Step 2 will be repeated for each additional rack.
4. Pipette will drop tip in waste bin.

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
4a0be6
