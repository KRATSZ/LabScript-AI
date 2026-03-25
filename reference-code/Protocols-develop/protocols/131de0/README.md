# Copy Number Variant (CNV) Plating

### Author
[Opentrons](https://opentrons.com/)



## Categories
*  PCR
	* PCR Prep

## Description
This protocol performs mastermix and DNA sample transfer to a custom 384-well plate. All DNA samples are transferred in quadruplicate in adjacent wells forming 2x2 well squares on the 384-well plate (12x8 squares mapping to the 12x8 input from the 96-well DNA plate), as in the following image:  

![transfer scheme](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/131de0/transfer_scheme.png)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* MicroAmp Optical 384-well plate
* USA Scientific 96 Well Plate 100 µL
* Custom single-channel reservoir 25ml (will span slots 4 and 1)
* [Opentrons P10 multi-channel GEN1 pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 10µl tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the mount side for your P10 multi-channel GEN1 pipette and the number of DNA samples to process (1-96, processed in columns of 8).
2. Download your protocol package.
3. Upload your custom labware and protocol script into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
131de0
