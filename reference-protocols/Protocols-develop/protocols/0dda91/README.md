# 16S Library pooling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Pooling

## Description
This protocol uses a .csv file to pool a calculated volume of each sample from a PCR plate into one or more 1.5 mL snapcap tube(s).  

Explanation of complex parameters below:
* `input .csv file`: Here, you should upload a .csv file formatted in the following way, being sure to include the header line:
```
 Sample Location,Qubits,Volume (ul) for ng: 70,Sample Destination,,,,,,,,,,,
A1,3.5,20.0,A1,,,,,,,,,,,
A2,15,4.7,A2,,,,,,,,,,,
```

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) - Not used in protocol but loaded so module can remain on the deck

### Labware
* [OT-2 Filter Tips, 20µL](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* [Opentrons Tough 0.2 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/tips-and-labware/)
* [4-in-1 Tube Rack Set](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Fisherbrand 2.0 mL Microcentrifuge Tubes with Locking Snap Cap](https://www.fishersci.com/shop/products/microcentrifuge-tubes-locking-snap-cap/14666313)

### Pipettes
* [P20 GEN2 Single Channel Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0dda91/deck.png)
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0dda91/liquids.png)

---

### Protocol Steps
1. Transfer 2-35 uL from the 96 well PCR plate to a 2 mL snap tube
2. Repeat across the entire plate according to the .csv file

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
0dda91
