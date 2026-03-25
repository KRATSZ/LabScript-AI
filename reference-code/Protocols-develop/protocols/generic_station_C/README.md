# Generic qPCR Setup Protocol (Station C)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Covid Workstation
	* qPCR Setup


## Description
This protocol automates setting up a plate for (reverse transcriptase) qPCR. Using the purified nucleic acid samples from Station B (RNA Extraction), the samples are then aliquoted and mixed with the reaction mix of the assay as outlined in our [article on automating Covid-19 testing](https://blog.opentrons.com/how-to-use-opentrons-to-test-for-covid-19/).</br>
</br>
Using a [Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette), this protocol will begin by transferring reaction mix (combination of master mix and primers/probes) from a 1.5mL tube in the 24-well aluminum block to the specified wells of a plate for qPCR. Then, using the [Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) or optional [Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette), samples will be transferred from their plate to the qPCR plate and mixed with the reaction mix.</br>
</br>
This protocol uses a custom labware definition. For more information on using labware with the OT-2, please see this [support article](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [Aluminum Block Set](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set))
* [Opentrons Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette), *optional*
* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) containing purified nucleic acid samples
* [NEST 1.5mL Microcentrifuge Tube](https://shop.opentrons.com/collections/tubes/products/nest-microcentrifuge-tubes) containing reaction mix(es)
* [Optical 96-Well qPCR Plate](https://www.thermofisher.com/order/catalog/product/N8010560#/N8010560)



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

The [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) should be placed in **slot 4** with the [96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) and [qPCR plate](https://www.thermofisher.com/order/catalog/product/N8010560#/N8010560) on top. The temperature module can be pre-cooled through the [Opentrons OT-2 Run App](https://opentrons.com/ot-app/)</br>
</br>
The reaction mix(es) (master mix/primers/probes/etc) should kept in the [microcentrifuge tube](https://shop.opentrons.com/collections/tubes/products/nest-microcentrifuge-tubes) and placed in the [24-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) (which can be put in the freezer beforehand to keep reagents cold) in **slot 5**. Up to three different reaction mixes can be used per plate and should be loaded in A1, B1, and C1.</br>
</br>
The [NEST PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) containing purified nucleic acid samples should be placed in **slot 1**. The samples should be filled in column order (ie, 3 samples would go in wells A1, B1, and C1).</br>
</br>
The [Opentrons Tiprack](https://shop.opentrons.com/collections/opentrons-tips) for the [Opentrons Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) should be placed in **slot 6**.</br>
</br>
If also using an [Opentrons Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) that is the same volumetrically as the single-channel pipette **and** the total number of tips that will be used is less than 96, then the same tiprack in slot 6 can be utilized. Otherwise, another tiprack should be placed in **slot 3**.</br>
</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Number of Samples**: Specify the number of samples to run. If using more than one reaction mix, the number of samples would be the same for each reaction mix. If using 1 reaction mix, the maximum number of samples would be 96; if using 2 reaction mixes, the maximum would be 48; and if using 3 reaction mixes, the maxium is 32.
* **Number of Reaction Mixes**: Select the number of reaction mixes (1, 2, or 3) that will be used.
* **Volume of Reaction Mix (µL)**: Specify the volume of the reaction mix(es) that should be added to each well of the qPCR plate.
* **Volume of Sample (µL)**: Specify the volume of the sample that should be transferred to each well of the qPCR plate.
* **Single-Channel Pipette Type (right mount)**: Select which single-channel pipette (p10, p50, or p20) that will be used. This pipette should be mounted to the right mount.
* **Multi-Channel Pipette Type (left mount)**: Select which multi-channel pipette (p10, p50, or p20) that will be used, if using (can also select *none*).
</br>
</br>
**Example layout: 48 samples with 2 reaction mixes**</br>
*note*: this configuration requires 98 tips, thus two tipracks are needed</br>
![Ex. 48 samples with 2 reaction mixes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/station_C/stationC_ex1.png)
</br>
</br>
**Example layout: 48 samples with 1 reaction mix and different pipettes**</br>
![Ex. 48 samples with 1 reaction mix and different pipettes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/station_C/stationC_ex2.png)
</br>
</br>

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
generic_station_A
