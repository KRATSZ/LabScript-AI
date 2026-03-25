# Lexogen QuantSeq 3'mRNA FWD NGS Library Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Lexogen QuantSeq

## Description
This protocol performs the [Lexogen QuantSeq 3'mRNA FWD NGS library prep](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2019-12-09/0313rnd/015UG009V0251_QuantSeq_Illumina.pdf) for up to 96 samples.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [NEST 0.1mL 96-well PCR plates, full skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons 4-in-1 tuberack set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 4x6 insert holding [NEST 1.5mL microcentrifuge tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* [Opentrons magnetic module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons temperature module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [4x6 aluminum block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) holding [NEST 1.5mL microcentrifuge tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* [Opentrons P20 GEN2 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons P300 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 10/20µl tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 50/300µl tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

4x6 tuberack (slot 2):
* tube A1: RS
* tube A2: SS1
* tube A3: SS2

4x6 aluminum block on temperature module (slot 7):
* tube A1: FS1
* tube A2: FS2/E1
* tube A3: PB
* tube A4: EB
* tube A5: PS
* tube A6: PCR/E3

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the respective mount sides for your P20 single-channel and P300 multi-channel pipettes and the number of samples to process.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6030b7
