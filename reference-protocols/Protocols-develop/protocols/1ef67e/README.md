# NCI Panel 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
	* Assay


## Description
This protocol represents one of several protocols that prepares a panel of set dilutions of primary antibodies and fluorophores. This protocol creates Panel 1. The following antibodies and fluorophores dilutions are prepared in this panel:

**Antibodies**
* CD4
* CD8
* FOXP3
* PD-L1 EL13N
* PAN CK
* KI-67

**Fluorophores**
* 520
* 570
* 540
* 620
* 650
* 690

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P10 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons P1000 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 10µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 1000µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* Custom Tube Holder for 6mL Tubes and Tubes
* [Bio-Rad 96 Well Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [50mL Tubes](https://shop.opentrons.com/collections/tubes/products/nest-50-ml-centrifuge-tube)
* [2mL Tubes](https://shop.opentrons.com/collections/tubes/products/nest-2-0-ml-microcentrifuge-tubes)
* [15mL Tubes](https://shop.opentrons.com/collections/tubes/products/nest-15-ml-centrifuge-tube)
* Antibodies
* Fluorophores



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: [Opentrons 1000µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)

Slot 2: Custom 6mL Tube Rack Holder and Tubes

Slot 3: [Bio-Rad 96 Well Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate), for sample aliquots

Slot 4: [Opentrons 10µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

Slot 5: [Opentrons 4-in-1 Tube Rack; 6x15mL, 4x50mL](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* A3: Antibody Dilutent (initial volume=50mL)
* A4: Fluorophore Dilutent (initial volume=50mL)

Slot 6: [Opentrons 4-in-1 Tube Rack; 24x2mL](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
*Setup with initial volumes*
* A1: 520, 75µL
* B1: 540, 75µL
* C1: 570, 75µL
* D1: 620, 75µL
* A2: 650, 75µL
* B2: 690, 75µL
* A3: CD3, 1000µL
* B3: CD4, 100µL
* C3: CD8, 100µL
* D3: CD20, 250µL
* A4: CD56, 1000µL
* B4: CD68, 100µL
* C4: CD163, 100µL
* D4: PD1, 100µL
* A5: PD-L1 EL13N, 100µL
* B5: FOXP3, 500µL
* C5: PAN CK, 1000µL
* D5: KI-67, 2000µL (Source 1)
* A6: KI-67, 2000µL (Source 2)
* B6: KI-67, 2000µL (Source 3)
* C6: KI-67, 2000µL (Source 4)
* D6: KI-67, 2000µL (Source 5)





### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol.
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
1ef67e
