# OT-2 Guided Walk-through

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Getting Started
	* OT-2 Guided Walk-through

## Description
Learn the OT-2 in under 10 minutes! This protocol will walk you through most of the OT-2 capabilities which include but are not limited to: touch tip, blow out, return tip, and distribute functions (for all functions covered in this protocol, see `Protocol Steps` section below).  

Understand what each OT-2 function does, and see it in real time before incorporating it into your own biology workflow.

Explanation of complex parameters below:
* `Well Plate`: Select which well plate will be loaded onto the deck.
* `Pipette`: Select which single-channel pipette will be loaded onto the deck.
* `Pipette Tips`: Select which pipette tips will accommodate the pipette you selected above.
`Pipette Mount`: Select which mount your pipette will be hosted on.
---

### Labware
* All well plates found in our [labware library](https://labware.opentrons.com/?category=wellPlate) can be used in this protocol.
* All Opentrons tip racks found in our [labware library](https://labware.opentrons.com/?category=tipRack) can be used in this protocol.

### Pipettes
* All Opentrons [Single channel pipettes](https://opentrons.com/pipettes/) can be used in this protocol.

### Reagents
* Load the plate with water or food coloring.

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/test_drive/Screen+Shot+2021-06-01+at+12.44.20+PM.png)

### Reagent Setup
Place your water/food coloring in the first column of the selected 96 well plate.
![reagent layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/test_drive/Screen+Shot+2021-06-01+at+12.44.41+PM.png)

---

### Protocol Steps
1. Move to function
2. Aspirate from various locations within well
3. Dispense various locations within well
4. Pause function
5. Mix function
6. Flow rate function
7. Touch tip function
8. Drop tip function
9. Return tip function
10. Airgap function (two ways)
11. Distribute function
12. Consolidate function

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
testdrive
