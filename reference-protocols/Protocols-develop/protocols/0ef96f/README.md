# Cherrypicking from .csv

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking

## Description
This protocol performs a custom cherrypicking from a 4x6 Opentrons tuberack containing 2ml Eppendorf tubes to an IDT 96-deepwell plate, and back to new tubes on the tuberack. The information for this workflow should be input in `.csv` file formatted as shown in the following example (**including headers**):

```
Label,Pos,nM,FC,Rxn,Vol,h2O,Tube
P_F3,A1,28.9,0.8,100,10,30,T1
P_B3,A2,28.32,0.8,100,10,,T1
P_FIP,A3,53.8,1.6,100,20,,T1
P_BIP,A4,82,1.6,100,20,,T1
P_LF,A5,32.5,0.4,100,5,,T1
P_LB,A6,29.4,0.4,100,5,,T1
P_F3,A7,28.9,0.8,100,10,35,T2
P_B3,A8,28.32,0.8,100,10,,T2
P_FIP,A9,53.8,1.6,100,20,,T2
P_BIP,A10,82,1.6,100,20,,T2
P_LF,A11,32.5,0.4,100,5,,T2
P_LB,A12,29.4,0.4,100,5,,T2
```

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* IDT 96-deepwell plate
* [Opentrons 4-in-1 tuberack set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 4x6 insert holding [2ml Eppendorf snapcap tubes](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Tubes-44515/Eppendorf-Safe-Lock-Tubes-PF-8863.html)
* [Opentrons P20- and P300-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 20 and 300ul tipracks](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

4x6 tuberack with 2ml Eppendorf tubes (slot 4)
![tuberack layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0ef96f/rack_setup.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Upload your `.csv` file formatted as shown above, and input the respective mount sides for your P20 and P300 GEN2 single-channel pipettes.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0ef96f
