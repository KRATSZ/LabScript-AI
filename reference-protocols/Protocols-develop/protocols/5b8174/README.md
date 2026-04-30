# Custom Multi-CSV Transfer for PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking

## Description
This protocol performs transfers of positive controls and patient samples to a 384 well plate loaded onto a temperature module. All labware and transfers can be controlled through the CSV files that are used as input for this protocol.

Explanation of complex parameters below:
* `P20 Single Channel Pipette Mount Position`: Choose the mount position of your pipette.
* `Control CSV File`: Upload the CSV file for controls here. You can download an [example CSV file here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5b8174/Control_updated_07302021.csv) OR follow the format directly below. **Note: The control source slot and destination slot are converted from the Eppendorf Rack format to the Opentrons 24 Tube Rack Format. Please refer to the Control Conversion Table at the end of this section.**
```
Rack,Sr.Barcode,,Dest.Barcode,Dest.List Name,
1,,PCRCTR15000004,,,
2,,,,,
3,,,,,
4,,,,,
,,,,,
Source Labware,Source Slot,Source Well,Dest Labware,Dest Slot,Dest Well
eppendorf_24_tuberack_generic_2.0ml_screwcap,1,D2,appliedbiosystems_384_wellplate_20ul,9,B1
eppendorf_24_tuberack_generic_2.0ml_screwcap,1,D3,appliedbiosystems_384_wellplate_20ul,9,A4
eppendorf_24_tuberack_generic_2.0ml_screwcap,1,D4,appliedbiosystems_384_wellplate_20ul,9,D2
```
* `Assembly CSV File`: Upload the CSV file for assembly/patient samples here. You can download an [example CSV file here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5b8174/Assembly.csv) OR follow the format directly below.
```
Rack,Sr.Barcode, ,Dest.Barcode,Dest.List Name,
1,,,,,
2,,,,,
3,,,,,
4,,,,,
,,,,,
Source Labware,Source Slot,Source Well,Dest Labware,Dest Slot,Dest Well
appliedbiosystems_96_wellplate_200ul_on_eppendorf_cooling_block,2,C11,appliedbiosystems_384_wellplate_20ul,6,B1
appliedbiosystems_96_wellplate_200ul_on_eppendorf_cooling_block,2,E11,appliedbiosystems_384_wellplate_20ul,6,A4
appliedbiosystems_96_wellplate_200ul_on_eppendorf_cooling_block,2,E11,appliedbiosystems_384_wellplate_20ul,6,D2
appliedbiosystems_96_wellplate_200ul_on_eppendorf_cooling_block,2,E11,appliedbiosystems_384_wellplate_20ul,6,E2
```
* `96 Well Plates Aspiration Height (mm)`: The aspiration height from the bottom of the well when aspirating from the assembly 96 well plates.

**Control Conversion Table**
```
Eppendorf Source Well, Destination Slot, Destination Well
A1,10,A1
A2,10,A2
A3,10,A3
A4,10,A4
A5,10,A5
A6,10,A6
B1,10,B1
B2,10,B2
B3,10,B3
B4,10,B4
B5,10,B5
B6,10,B6
C1,10,C1
C2,10,C2
C3,10,C3
C4,10,C4
C5,10,C5
C6,10,C6
D1,10,D1
D2,10,D2
D3,10,D3
D4,10,D4
D5,10,D5
D6,10,D6
E1,7,A1
E2,7,A2
E3,7,A3
E4,7,A4
E5,7,A5
E6,7,A6
F1,7,B1
F2,7,B2
F3,7,B3
F4,7,B4
F5,7,B5
F6,7,B6
G1,7,C1
G2,7,C2
G3,7,C3
G4,7,C4
G5,7,C5
G6,7,C6
H1,7,D1
H2,7,D2
H3,7,D3
H4,7,D4
H5,7,D5
H6,7,D6
I1,4,A1
I2,4,A2
I3,4,A3
I4,4,A4
I5,4,A5
I6,4,A6
J1,4,B1
J2,4,B2
J3,4,B3
J4,4,B4
J5,4,B5
J6,4,B6
K1,4,C1
K2,4,C2
K3,4,C3
K4,4,C4
K5,4,C5
K6,4,C6
L1,4,D1
L2,4,D2
L3,4,D3
L4,4,D4
L5,4,D5
L6,4,D6
```
---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Opentrons 20 uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

### Pipettes
* [Opentrons P20 Single Channel GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

---

### Deck Setup
* If the deck layout of a particular protocol is more or less static, it is often helpful to attach a preview of the deck layout, most descriptively generated with Labware Creator. Example:
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5b8174/5b8174_new_layout.png)

---

### Protocol Steps
1. Using information from Control CSV file, transfer 1.5uL of positive control from the (Source Labware, Source Slot, Source Well) to the (Dest Labware, Dest Slot, Dest Well), as indicated in the CSV. Change tip between each transfer.
2. Using information from Assembly CSV file, transfer 1.5uL of patient DNA from the (Source Labware, Source Slot, Source Well) to the (Dest Labware, Dest Slot, Dest Well), as indicated in the CSV. Change tip between each transfer.


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
5b8174