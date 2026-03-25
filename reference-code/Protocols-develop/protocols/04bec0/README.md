# Normalization


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Normalization


## Description
This protocol performs a custom normalization and LDS addition across 3 sets of 1.5ml tuberacks using P300 and P1000 single-channel pipettes. The normalization volumes are automatically calculated.

The input .csv file specifying the biomasses of all sample input should be formatted as follows ***including first row for column names and first column for row names***. Note that wells that should be ignored should contain a `0` value:

```
,1,2,3,4,5,6,7,8
A,0,0,0,0,0,0,0,0
B,0,0,0,0,0,0,0,0
C,80,60.72,82.79,207.23,370.24,265.78,270.34,342.88
D,70,56.65,99.74,249.64,340.56,285.08,294,366.09
E,117.17,162.28,88.7,135.69,322.46,321,285.73,375.51
F,130.01,172.35,93.48,136.36,326.26,285.79,316.29,344.37
```

You can also download a template from [this link](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04bec0/ex.csv).


### Labware
* Beckman Fed Batch Plate #Beckman Coulter
* [Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 6 Tube Rack with Falcon 50 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* Opentrons 96 Filter Tip Rack 200 µL
* Opentrons 96 Filter Tip Rack 1000 µL


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P1000 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04bec0/deck.png)


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
04bec0
