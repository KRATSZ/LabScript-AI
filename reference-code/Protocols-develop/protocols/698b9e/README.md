# PCR Prep with 1.5 mL Tubes Part 1 - Plate Filling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol is part one of a two part series for performing a custom PCR prep with 1.5 mL Falcon conical tubes. Find Part 2 of the protocol here:

* [PCR Prep with 1.5 mL Tubes Part 2 - Adding Sample](https://protocols.opentrons.com/protocol/698b9e-part2)

This protocol fills one of two plates with either reaction buffer or mastermix as specified by the user. The user can also specify how many plates they would like to fill with buffer, or mastermix. Plates should then be kept in cold storage, ready for use as saliva samples come in.


Explanation of complex parameters below:
* `Number of Plates`: Specify the number of plates you want to populate with reagent.
* `Reagent`: Specify whether you would like to fill the number of plates selected above with mastermix, or buffer. 80ul will be transferred if `Buffer` is selected, while 7.6ul will be transferred to each well in every plate if `Mastermix` is selected. The P300 Multi Channel pipette is used for `Buffer`, while the P20 Single Channel Pipette is used for `Mastermix`.
* `P300 Multi Channel Mount`: Specify which side (left or right) to mount the P300 Multi Channel Pipette.  
* `P20 Single Channel Mount`: Specify which side (left or right) to mount the P20 Single Channel Pipette.  


---

### Labware
* [Opentrons Filter Tip Racks 20ul](https://shop.opentrons.com/collections/opentrons-tips?_gl=1*5kaie6*_gcl_aw*R0NMLjE2MTk1Mjk1OTMuQ2p3S0NBanc3SjZFQmhCREVpd0E1VVVNMmhrMnp2YjM4UmRhNzB6S2NyWWdmU3pSTUhhdTI5UmxCV01UMFp2MW1WdFZhY1VyWFRnQ3V4b0NBQ3dRQXZEX0J3RQ..*_ga*ODQ1NDAxMzU2LjE2MTIxOTA0Nzc.*_ga_GNSMNLW4RY*MTYyMDA0OTcwOC4yMDguMS4xNjIwMDUwNDc1LjA.&_ga=2.187346848.986719466.1619449162-845401356.1612190477&_gac=1.82396900.1619529593.CjwKCAjw7J6EBhBDEiwA5UUM2hk2zvb38Rda70zKcrYgfSzRMHau29RlBWMT0Zv1mVtVacUrXTgCuxoCACwQAvD_BwE)
* [Opentrons Filter Tip Racks 200ul](https://shop.opentrons.com/collections/opentrons-tips?_gl=1*5kaie6*_gcl_aw*R0NMLjE2MTk1Mjk1OTMuQ2p3S0NBanc3SjZFQmhCREVpd0E1VVVNMmhrMnp2YjM4UmRhNzB6S2NyWWdmU3pSTUhhdTI5UmxCV01UMFp2MW1WdFZhY1VyWFRnQ3V4b0NBQ3dRQXZEX0J3RQ..*_ga*ODQ1NDAxMzU2LjE2MTIxOTA0Nzc.*_ga_GNSMNLW4RY*MTYyMDA0OTcwOC4yMDguMS4xNjIwMDUwNDc1LjA.&_ga=2.187346848.986719466.1619449162-845401356.1612190477&_gac=1.82396900.1619529593.CjwKCAjw7J6EBhBDEiwA5UUM2hk2zvb38Rda70zKcrYgfSzRMHau29RlBWMT0Zv1mVtVacUrXTgCuxoCACwQAvD_BwE)
* [Nunc™ 96-Well Polypropylene Storage Microplates](https://www.thermofisher.com/order/catalog/product/249944?SID=srch-hj-249944#/249944?SID=srch-hj-249944)
* [MicroAmp™ Fast Optical 96-Well Reaction Plate with Barcode, 0.1 mL](https://www.thermofisher.com/order/catalog/product/4346906?SID=srch-srp-4346906#/4346906?SID=srch-srp-4346906)

### Pipettes
* [P20 Single Gen2 Pipette](https://opentrons.com/pipettes/)
* [P300 Single Gen2 Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
* Deck setup if running 9 plates. If selecting less than 9 plates, fill the deck slots in numerical order starting from Deck Slot 3.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/698b9e/Screen+Shot+2021-05-06+at+1.22.06+PM.png)

### Reagent Setup
* Example of reservoir filled with buffer solution for a 9-plate setup. Each reservoir well corresponds to one plate. Please ensure at least 7.7 mL of solution is in each reservoir well to fully populate each plate. If running mastermix, only the first reservoir well needs to be filled (A1).

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/698b9e/Screen+Shot+2021-05-06+at+1.22.36+PM.png)


---

### Protocol Steps
1. Reagent (mastermix or buffer) is aspirated from the reservoir.
2. Reagent (mastermix or buffer) is dispensed to each well of all plates loaded onto the deck.

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
698b9e
