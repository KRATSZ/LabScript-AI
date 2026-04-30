# Covid-19 qPCR Prep (Station C)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Covid Workstation
	* qPCR Setup


## Description
This protocol creates a custom qPCR prep protocol for Covid-19 diagnostics. The input into this protocol is an elution plate of purified RNA, and the output is a PCR plate containing the samples mixed with mastermix.
Using a [Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette), this protocol will begin by creating reaction mix in a 2ml tube. The mix is then distributed to a PCR strip. Then, using the [Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette), samples will be transferred from their plate to the qPCR plate and mixed with the reaction mix.

If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [Aluminum Block Set](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set))
* [Opentrons P300 Single-Channel GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons P20 Multi-Channel GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) containing purified nucleic acid samples
* [2ml NEST screwcap tubes or equivalent](https://shop.opentrons.com/collections/tubes/products/nest-microcentrifuge-tubes) containing reaction mix(es)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

chilled 24-well aluminum block for 2ml tubes (slot 5):  
![tubeblock](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1ccd23/stationCtubeblock.png)

Allplex 2019-nCoV Assay (17µl/sample total):  
* reagent 1: 2019-nCov MOM (5µl/sample)
* reagent 2: RNase-free water (5µl/sample)
* reagent 3: 5X Real-time One-step Buffer (5µl/sample)
* reagent 4: Real-time One-step Enzyme (2µl/sample)

Allplex SARS-CoV-2 Assay (15µl/sample total):  
* reagent 1: SARS2 MOM (5µl/sample)
* reagent 2: EM8 (5µl/sample)
* reagent 3: RNase-free water (5µl/sample)

Seegene Real-time One-step RT-PCR:  
* reagent 1: SC2FabR MOM (5µl/sample)
* reagent 2: EM8 (5µl/sample)

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
1ccd23
