# Omega Biotek Mag-Bind Viral RNA XPress Kit (200µl sample input)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Covid Workstation
	* RNA Extraction

## Description
This protocol fully automates the [Omega Biotek Mag-Bind Viral RNA XPress Kit](https://www.omegabiotek.com/product/viral-rna-extraction-kit-mag-bind-viral-rna-xpress/?gclid=Cj0KCQjwlOmLBhCHARIsAGiJg7l7b_wVehYVQaXLe_wBJzEiE91FvrAfySaQaLjZ6VpLZzkCRcJLl6oaAoSjEALw_wcB). This specific protocol allows the user to manipulate the number of samples, elution volume, as well as tip parking for ultimate reuse (saving up to 4 tip boxes per run).

![volume reqs](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/omega-biotek-xpress/Screen+Shot+2021-10-28+at+7.39.52+PM.png)

Before you begin:
1. Pre-cool the Temperature Module in the Opentrons App to 4°C
2. Create the Binding MasterMix
![volumes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/omega-biotek-xpress/Screen+Shot+2021-10-28+at+6.58.42+PM.png)
3. Add the Binding Mastermix, RMP Buffer, Nuclease Free H20, and Lysis Buffer to the 12 well
reservoir
4. Create the freshly diluted 80% ethanol and add it to the 1 well reservoir in slot 2
5. Place the deep well plate filled with samples on top of the magnetic module in slot 4.
6. Add a 96 well aluminum block and the 96 well PCR plate or PCR strip tubes on top of
the Temperature Module in slot 1
The final plate of eluates/extractions will be found on top of the temperature module in slot 1.

Explanation of complex parameters below:
* `Number of Samples`: Select the number of samples for this run.
* `Park tips?`: if True for “tiprack parking,” tips used for the same buffers with the same samples will be
reused where 1 tiprack turns into a tiprack where used tips are “parked”. This method has low risk of
contamination and is highly recommended to avoid pauses to reuse tips. If selected, the parked tiprack slot is on slot 7.
* `Elution Volume`: Specify the elution volume for this run.
* `P300 Multi-Channel Mount`: Specify which mount (left or right) to host the P300 multi-channel pipette.



---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
[NEST 2mL deep well plate (input with samples)](https://shop.opentrons.com/collections/lab-plates)
[200μl filter tip racks (10 x 200μl if you select false for tiprack parking)](https://shop.opentrons.com/collections/opentrons-tips)
[NEST 1 well reservoir](https://shop.opentrons.com/collections/reservoirs)
[NEST 12 well reservoir](https://shop.opentrons.com/collections/reservoirs)
[NEST 96 well aluminum block 100ul](https://shop.opentrons.com/collections/lab-plates)


### Pipettes
* [8-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Reagents
* [Mag-Bind® Viral RNA Xpress Kit](https://www.omegabiotek.com/product/viral-rna-extraction-kit-mag-bind-viral-rna-xpress/?gclid=Cj0KCQjwlOmLBhCHARIsAGiJg7l7b_wVehYVQaXLe_wBJzEiE91FvrAfySaQaLjZ6VpLZzkCRcJLl6oaAoSjEALw_wcB)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/omega-biotek-xpress/Screen+Shot+2021-10-28+at+6.48.16+PM.png)

### Reagent Setup
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/469c70/Screen+Shot+2021-12-03+at+8.51.12+AM.png)


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
omega-biotek-xpress
