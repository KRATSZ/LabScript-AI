# Saliva sample transfer from source to target well plate
### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* PCR prep

## Description
This protocol transfers 5 µL of saliva samples from a source to a target 96 well plate using a 20 µL multi-channel pipette.
The protocol lets the user control the height of aspiration/dispension from the bottom of the samples and target wells, as well as the flow rate of aspiration and dispension.


Explanation of parameters below:
* `Number of samples to transfer`: How many samples to transfer from the source to the target plate
* `Aspiration flow rate (µL/s)`: rate of aspiration in microliters per second
* `Dispension flow rate (µL/s)`: rate of dispension in microliters per second
* `Aspiration height from the bottom of the tubes (mm)`: Height from the bottom of the tubes to aspirate from in mm
* `Dispension height from the bottom of the tubes (mm)`: Height from the bottom of the plate wells to dispense from in mm
* `(Optional) Temperature module with aluminum block`: Parameter to indicate whether you are using a temperature module with an aluminum block to put your source plate on
* `Set temperature of the temperature module`: Temperature to set on the temperature module in degrees C
* `Amount of time to keep the pipette in the tube after aspiration (s)`: How many seconds to wait before withdrawing the pipette from the tube after aspiration

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Stellar Scientific 96 well plate](https://www.stellarscientific.com/96-well-low-profile-fast-type-pcr-plate-with-raised-rim-edge-0-1ml-rnase-and-dnase-free-clear-100-cs/)

### Pipettes
* [20 µL multi-channel pipette gen2](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [20 µL filter tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/300073/deck2.jpg)

---

### Protocol Steps
1. If a temperature module is on the deck the first step is to set the temperature according to the parameter.
2. Samples are transferred from the source plate to the target plate, in the manner specified by the parameter settings.

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
300073-2
