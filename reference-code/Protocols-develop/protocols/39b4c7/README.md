# Reformat 96 Well Plates to 384 Well Plate for qPCR

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
    * qPCR setup

## Description
Reformat up to four 96 well plates into a 384 well PCR plate for downstream qPCR. This protocol will also add mastermix to the necessary wells and then transfer patient samples to the corresponding wells.

![384 Grid](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/39b4c7/39b4c7_384_layout.png)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons 20uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 20uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [KingFisher 96 Deep Well Plate 2mL](https://www.thermofisher.com/order/catalog/product/95040450#/95040450)
* [MicroAmp™ Optical 384-Well Reaction Plate with Barcode](https://www.thermofisher.com/order/catalog/product/4309849?SID=srch-srp-4309849#/4309849?SID=srch-srp-4309849)
* [Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://shop.opentrons.com/products/tube-rack-set-1?_ga=2.232823964.387689945.1619373905-1181961818.1604785212&_gl=1%2Akkqpyx%2A_ga%2AMTE4MTk2MTgxOC4xNjA0Nzg1MjEy%2A_ga_GNSMNLW4RY%2AMTYxOTQ1ODk2Mi4xOTguMS4xNjE5NDU5NTQzLjA.)
* [P20 Single Channel GEN2](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Setup**
![Deck Layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/39b4c7/39b4c7_deck_layout.png)

**Note**: A full run with 4 plates with a master mix transfer volume of 10 uL will require 3,760 uL of master mix. This is divided into 3 tubes in the picture above. There is a parameter below that asks for the `Master Mix Volume per Tube`. By default this is set to 1400 uL (**Recommendation: Always add more than 1400 uL to prevent aspirating air**) in order to account for dead volume. You can adjust this as needed and the protocol will automatically determine how many tubes it needs. 

**For Example**: If the `Master Mix Volume per Tube` is set to 1000 uL the protocol will determine 4 tubes are needed (A1, B1, C1, D1) with at least 1000 uL in each tube for a run with four full plates. The last tube does not require a full 1000 uL volume; it would need a bit more than the difference (~760 uL). 

**Protocol Steps**

1. Transfer 10 uL of Master Mix from A1 of the Tube Rack to A1 of the 384 well plate.
`Step 1 will repeat for all samples into the corresponding wells using the same tip.`
2. Transfer 10 uL of patient sample from A1 of Plate 1 to A1 of the 384 Well PCR plate.
`Step 2 will repeat for all patient samples into the corresponding wells using a new tip each time.`

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

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
39b4c7