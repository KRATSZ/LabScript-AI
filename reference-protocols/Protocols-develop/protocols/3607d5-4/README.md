# Normalization and Pooling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description

Links:  
* [SPRI 1 & 2](./3607d5-2)
<br />
<br />
* [PCR2 Setup](./3607d5)
<br />
<br />
* [SPRI 3](./3607d5-3)
<br />
<br />
* [Normalization and Pooling](./3607d5-4)
<br />
<br />
* [Rerack](./3607d5-5)


This is a custom normalization pooling protocol from up to 12 sources to a pooling tube. The input .csv for RSB volume specification should be specified as follows:

```
well,volume rsb
A1,200
B1,15
...
```

---

### Labware
* [Opentrons 20µl Tiprack](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 300µl Tiprack](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 96 Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [Opentrons 4-in-1 Tuberack Set](https://shop.opentrons.com/4-in-1-tube-rack-set/)

### Pipettes
* [P20 Multi GEN2 Pipette](https://opentrons.com/pipettes/)
* [P300 Multi GEN2 Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
* green: RSB  
* blue: samples    
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3607d5/deck4.png)

---

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
3607d5
