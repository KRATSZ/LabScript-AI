# Custom Slide Transfer Protocol

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol automates spotting of slides, using a custom labware piece that holds 4 slides, each containing 21 spots.</br>
</br>
The protocol begins by adding 1µL to each spot of the four slides, using solutions in A2, A3, A4, and A5 of a 1.5mL eppendorf tube in an Opentrons Tube Rack in slot 2 (changes tip between each solution).</br>
</br>
The protocol concludes by adding 1µL of solution to each spot of the slides in triplicate. Cycling through tubes A6 of the tuberack in slot 2 and tubes in A1-A6 in slot 3, the p20 will make each transfer and discard tip after each transfer. This behavior continues with rows B, C, and D for slides 2, 3, and 4, respectively.</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 10/20µL Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [1.5mL Microcentrifuge Tube](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* Custom Adaptor that contains 4 [PTFE Printed Slides](https://www.2spi.com/item/02289-ab/)



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)


**Deck Setup**</br>
</br>
Slot 1: [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 2: [Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 1.5mL eppendorf tubes</br>
A2: Solution for all spots of slide 1</br>
A3: Solution for all spots of slide 2</br>
A4: Solution for all spots of slide 3</br>
A5: Solution for all spots of slide 4</br>
A6: Solution for first 3 spots of slide 1</br>
B6: Solution for first 3 spots of slide 2</br>
C6: Solution for first 3 spots of slide 3</br>
D6: Solution for first 3 spots of slide 4</br>
</br>
Slot 3: [Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 1.5mL eppendorf tubes</br>
A1-A6: Solution for slide 1</br>
B1-B6: Solution for slide 2</br>
C1-C6: Solution for slide 3</br>
D1-D6: Solution for slide 4</br>
</br>
Slot 5: Custom Adaptor that contains 4 [PTFE Printed Slides](https://www.2spi.com/item/02289-ab/)</br>


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol package.
2. Upload custom labware definition (if running for first time).
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
1f8b55
