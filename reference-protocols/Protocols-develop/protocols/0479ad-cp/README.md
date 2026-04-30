# Normalization from Plates with a Single-Channel Pipette


### Author
[Breakthrough Genomics](https://opentrons.com/)




## Categories
* Sample Prep
	* Normalization


## Description
This protocol performs normalization on up to 96 samples in PCR plates using Opentrons single-channel pipettes. The `Volumes CSV` download parameter should be formatted as the following:

```
sample,vol_dna,vol_water
A1,23.4,11.6
B1,4.9,21.1
C1,21.6,4.4
D1,15.1,10.9
E1,19.1,6.9
F1,18.6,7.4
G1,10.7,15.3
H1,21.9,4.1
A2,19.1,6.9
B2,0.4,25.6
C2,24.0,2.0
D2,6.1,19.9
E2,10.7,15.3
F2,24.2,1.8
G2,6.1,19.9
H2,3.0,23.0
...
```


### Modules
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* thermofisher 96 well pcr plate semi-skirted 200 uL + plastic adapter
* thermofisher 96-well PCR Plate semi-skirted 200 uL + aluminum block
* [USA Scientific 12 Well Reservoir 22 mL #1061-8150](https://www.usascientific.com/12-channel-automation-reservoir.aspx)
* Opentrons 96 Filter Tip Rack 200 µL
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad-cp/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0479ad-cp/reagents.png)



### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
0479ad-cp
