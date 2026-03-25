# Cherrypicking with Source and Destination

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Featured
	* Cherrypicking

## Description
This protocol utilizes a user-specified CSV to transfer sample using a variety of labware. With this protocol you have the ability to choose between the following:

* Starlab Deepwell Plate
* Eppendorf 2mL Tube in Tube Rack
* Eppendorf 1.5mL Tube in Tube Rack
* NEST 96-Well, 200µL Flat
* NEST 96-Well, 100µL PCR
* BioRad 96-Well, 200µL PCR
* Corning 96-Well, 360µL Flat
* Corning 384-Well, 112µL Flat
* USA Scientific 96-Deepwell, 2.4mL

With the destination labware providing the same options as source labware.

Explanation of complex parameters below:
* `Volumes CSV`: Here, you should upload a .csv file formatted in the following way, being sure to include the header line:

`Source Well` | `Volume` | `Destination Well`

**Note about CSV**: The first column is dedicated to the header of the CSV; thus, the first row of data should occupy cells 'A2', 'B2', and 'C2' in the document.

* `Pipette Model`: Select which pipette you will use for this protocol.
* `Pipette Mount`: Specify which mount your single-channel pipette is on (left or right).
* `Source Labware Type`: Select which (destination) labware you will use for this protocol.
* `Destination Labware Type`: Select which (destination) labware you will use for this protocol.
* `Tip Use Strategy`: Select whether you would like to use the same tip or a new tip for each transfer.

---

### Labware
* Starlab Deepwell Plate
* [Eppendorf 2mL Tube in Tube Rack](https://labware.opentrons.com/?category=tubeRack)
* [Eppendorf 1.5mL Tube in Tube Rack](https://labware.opentrons.com/?category=tubeRack)
* [NEST 96-Well, 200µL Flat](https://labware.opentrons.com/?category=wellPlate)
* [NEST 96-Well, 100µL PCR](https://labware.opentrons.com/?category=wellPlate)
* [BioRad 96-Well, 200µL PCR](https://labware.opentrons.com/?category=wellPlate)
* [Corning 96-Well, 360µL Flat](https://labware.opentrons.com/?category=wellPlate)
* [Corning 384-Well, 112µL Flat](https://labware.opentrons.com/?category=wellPlate)
* [USA Scientific 96-Deepwell, 2.4mL](https://labware.opentrons.com/?category=wellPlate)

### Pipettes
* [Opentrons Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7a3e4b/Screen+Shot+2021-04-29+at+1.49.22+PM.png)


---

### Protocol Steps
1. Pipette will aspirate a user-specified volume at the designated labware and well according to the imported csv file.
2. Pipette will dispense this volume into user-specified labware and well according to the imported csv file.
3. Steps 1 and 2 repeated over the duration of the CSV file. 

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
7a3e4b
