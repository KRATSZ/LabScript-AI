# Lyra Direct Covid-19 Mastermix Distribution

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol automates the mastermix distribution portion of the [Lyra Direct SARS-CoV-2 Assay](https://www.quidel.com/molecular-diagnostics/lyra-direct-sars-cov-2-assay).</br>
Using an [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette), this protocol will transfer 15µL of mastermix from a 1.5mL eppendorf tube to the specified number of wells in a standard 96-well PCR plate.
</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Temperature Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [96-Well Aluminum Block for Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 20µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* Eppendorf 1.5mL Microcentrifuge Tube
* [Lyra Direct SARS-CoV-2 Assay Kit](https://www.quidel.com/molecular-diagnostics/lyra-direct-sars-cov-2-assay)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
Slot 2: [Opentrons 20µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 3: [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) and [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)</br>
</br>
Slot 6: [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 24-Tube Topper, containing eppendorf 1.5mL microcentrifuge tube containing mastermix in position D1


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol bundle.
2. Upload [custom labware definition](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols), if needed.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
29effa-mastermix
