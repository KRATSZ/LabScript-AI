# Plate Filling Sample in AB 384 Well Plate

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol transfers sample from [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) to [Applied Biosystems MicroAmp 384-well plates](https://www.thermofisher.com/order/catalog/product/4343370#/4343370) with mastermix. **Update**: this protocol has been updated to accommodate the SSI 384-well plate as well.</br>
</br>
The protocol can fill one or two, 384-well plates. The [P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes) will aspirate 5µL from each well of the [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) and dispense 2.5µL into two wells of the (A1 --> A1/B1; B1 --> C1/D1; etc.)</br>
</br>
**Update (10/22/20):** The protocol will now aspirate 10µL and dispense 5µL into two wells.</br>
</br>
**Update (11/2/20):** The protocol will now aspirate 20µL and dispense 10µL into two wells. Additionally, the option to use the p300-multi pipette has been added.
**Updated (11/12/20):** A new parameter has been added that allows the user to input the volume (in µL) of sample that should be transferred. The pipette will aspirate 2x the volume and dispense into two wells.


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Applied Biosystems MicroAmp 384-Well Plate](https://www.thermofisher.com/order/catalog/product/4343370#/4343370) or SSI 384-Well Plate with mastermix
* [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) with samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slots 1: [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

Slot 2: [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) with samples

Slot 3: [Applied Biosystems MicroAmp 384-Well Plate](https://www.thermofisher.com/order/catalog/product/4343370#/4343370) or SSI 384-Well Plate with mastermix

Slot 4: [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

Slot 5: [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) with samples

Slot 6: [Applied Biosystems MicroAmp 384-Well Plate](https://www.thermofisher.com/order/catalog/product/4343370#/4343370) or SSI 384-Well Plate with mastermix (if filling two plates)

Slot 7: [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips) (if filling two plates)

Slot 8: [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) with samples (if filling two plates)

Slot 9: *empty*

Slot 10: [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips) (if filling two plates)

Slot 11: [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) with samples (if filling two plates)

</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Pipette Type**: Select which pipette will be used
* **Pipette Mount**: Select which mount (left or right) the pipette is attached to.
* **Sample Volume (uL)**: Input the sample volume
* **How many 384-well plates**: Specify the number of 384-well plates to fill
* **Plate (384-Well) Type**: Specify the type of 384-well plates that are being used



### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol. For help, please see [this article](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
5c24e2
