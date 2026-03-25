# PCR Prep with 1.5 mL Tubes Part 2 - Adding Sample

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol is part two of a two part series for performing a custom PCR prep with 1.5 mL Falcon conical tubes. Find Part 1 of the protocol here:

* [PCR Prep with 1.5 mL Tubes Part 1 - Plate Filling](https://protocols.opentrons.com/protocol/698b9e)

This protocol makes a saliva and buffer solution, and then transfers this solution to a mastermix plate for further processing. 


Explanation of complex parameters below:
* `Number of Samples`: Specify the number of sample tubes you will use over this run. After samples from all tubes in the tube rack have been moved to the buffer plate, the protocol will pause and ask for the user to replace the tubes. For example, a value of `32` for `Number of Samples` would ask the user to replace the tube rack once (after 15 samples), and the OT-2 will then only aspirate from the first two tubes after replacement.
* `Aspirate Saliva Delay Time (in seconds)`: Select the amount of time to delay after aspirating saliva or saliva/buffer solution to allow for full achievement of aspiration.
* `P300 Multi Channel Mount`: Specify which side (left or right) to mount the P300 Multi Channel Pipette.  
* `P20 Single Channel Mount`: Specify which side (left or right) to mount the P20 Single Channel Pipette.  


---

### Labware
* [Opentrons Filter Tip Racks 20ul](https://shop.opentrons.com/collections/opentrons-tips?_gl=1*5kaie6*_gcl_aw*R0NMLjE2MTk1Mjk1OTMuQ2p3S0NBanc3SjZFQmhCREVpd0E1VVVNMmhrMnp2YjM4UmRhNzB6S2NyWWdmU3pSTUhhdTI5UmxCV01UMFp2MW1WdFZhY1VyWFRnQ3V4b0NBQ3dRQXZEX0J3RQ..*_ga*ODQ1NDAxMzU2LjE2MTIxOTA0Nzc.*_ga_GNSMNLW4RY*MTYyMDA0OTcwOC4yMDguMS4xNjIwMDUwNDc1LjA.&_ga=2.187346848.986719466.1619449162-845401356.1612190477&_gac=1.82396900.1619529593.CjwKCAjw7J6EBhBDEiwA5UUM2hk2zvb38Rda70zKcrYgfSzRMHau29RlBWMT0Zv1mVtVacUrXTgCuxoCACwQAvD_BwE)
* [Opentrons Filter Tip Racks 200ul](https://shop.opentrons.com/collections/opentrons-tips?_gl=1*5kaie6*_gcl_aw*R0NMLjE2MTk1Mjk1OTMuQ2p3S0NBanc3SjZFQmhCREVpd0E1VVVNMmhrMnp2YjM4UmRhNzB6S2NyWWdmU3pSTUhhdTI5UmxCV01UMFp2MW1WdFZhY1VyWFRnQ3V4b0NBQ3dRQXZEX0J3RQ..*_ga*ODQ1NDAxMzU2LjE2MTIxOTA0Nzc.*_ga_GNSMNLW4RY*MTYyMDA0OTcwOC4yMDguMS4xNjIwMDUwNDc1LjA.&_ga=2.187346848.986719466.1619449162-845401356.1612190477&_gac=1.82396900.1619529593.CjwKCAjw7J6EBhBDEiwA5UUM2hk2zvb38Rda70zKcrYgfSzRMHau29RlBWMT0Zv1mVtVacUrXTgCuxoCACwQAvD_BwE)
* [Nunc™ 96-Well Polypropylene Storage Microplates](https://www.thermofisher.com/order/catalog/product/249944?SID=srch-hj-249944#/249944?SID=srch-hj-249944)
* [MicroAmp™ Fast Optical 96-Well Reaction Plate with Barcode, 0.1 mL](https://www.thermofisher.com/order/catalog/product/4346906?SID=srch-srp-4346906#/4346906?SID=srch-srp-4346906)
* [NEST 12-Well Reservoir, 15 mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)

### Pipettes
* [P20 Single Gen2 Pipette](https://opentrons.com/pipettes/)
* [P300 Single Gen2 Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/698b9e/Screen+Shot+2021-05-06+at+1.49.33+PM.png)






---

### Protocol Steps
1. Saliva is added to buffer plates and mixed 6 times. User is directed to replace tubes until `Number of Samples` number is reached.
2. Diluted saliva is then added to mastermix plate and mixed.

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
698b9e-part2
