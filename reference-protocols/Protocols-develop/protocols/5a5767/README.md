# 384-well Plate One-to-One Transfer

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol moves up to 384 samples from 1 source plate to 1 destination plate using a P50-multichannel GEN1 pipette. The source plate is a Greiner Bio-One 384-well plate, and the destination plate can be either a Corning 384-well plate or a Bio-Rad 384-well plate. Samples are transferred across row A (A1, C1, E1, G1, I1, K1, M1, O1; A2, C2, E2, G2, I2, K2, M2, O2; etc.), then across row B (B1, D1, F1, H1, J1, L1, N1, P1; B2, D2, F2, H2, J2, L2, N2, P2; etc.).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 4.0.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P50 Multi-Channel Pipette GEN1](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 96 Tiprack 300ul](https://shop.opentrons.com/collections/opentrons-tips)
* [Greiner Bio-One 384 Well Plate 100 µL #781720](https://www.gbo.com/en_US.html)
* [Corning 384 Well Plate 20 µL #4511](https://ecatalog.corning.com/life-sciences/b2c/EUOther/en/Microplates/Assay-Microplates/384-Well-Microplates/Corning®-384-well-Solid-Black-and-White-Polystyrene-Microplates/p/4511)
* [Bio-Rad 384 Well Plate 50 µL #HSR4801](https://www.bio-rad.com/en-us/sku/hsr4801-hard-shell-384-well-pcr-plates-clear-clear-barcoded?ID=HSR4801)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".


### Additional Notes

If you’d like to request a protocol supporting multiple plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an applications engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
5a5767
