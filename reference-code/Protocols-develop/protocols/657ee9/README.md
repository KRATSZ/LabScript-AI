# Oncomine Focus Assay - Pt 1: Target Amplification

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Oncomine Focus Assay

## Description
This is the first part in a multi-part protocol designed to automate the Oncomine Focus Assay. For a detailed description of the manual protocol, please see [this resource.](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2022-01-27/kk23ns4/MAN0015819_Part1_OFAv1S5FTLibraryPrep_UG.pdf)

In this protocol, the OT-2 automates the 'Target Amplification' portion of the protocol. Using the complex parameters described below, the user can specify which, if any, modules they are using and select from different options pertaining to RNA/cDNA and DNA.

Explanation of complex parameters below:
* **Number of Samples**: Specify the number of samples.
* **Master Mix Transfer Volume**: Select the volume of mastermix to transfer to the samples. 10µL is for cDNA synthesis and the other options are for DNA.
* **Module for Destination Plate**: Select which module you are using for the destination plate (containing samples). If you are not using the [Opentrons Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module), you will be prompted to remove the plate after liquid handling to an off-deck thermal cycler.
* **Number of Cycles**: If using the [Opentrons Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module), you can specify the number of cycles. For more information, please see [the manual](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2022-01-27/kk23ns4/MAN0015819_Part1_OFAv1S5FTLibraryPrep_UG.pdf).
* **Module for Reagent Plate**: Select which module you will use for the plate containing mastermix.
* **P20-Multi Mount**: Select which mount the [P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/) is attached to.  

---

### Modules
* [Optional] [Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Optional] [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)


### Labware
* [NEST 96-Well PCR Plates](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* [Opentrons 20µL Filter Tip Rack](https://shop.opentrons.com/opentrons-20ul-filter-tips/)


### Pipettes
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Reagents
* [Oncomine Focus Assay](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2022-01-27/kk23ns4/MAN0015819_Part1_OFAv1S5FTLibraryPrep_UG.pdf)


---

### Deck Setup
**Slot 7**: [Plate]((https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)) containing samples (Destination Plate). Can be on [Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) or the [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module).</br>
</br>
**Slot 4**: [Plate]((https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)) containing master mix in column 1. Can be on [Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck).</br>
</br>
**Slot 3**: [Opentrons 20µL Filter Tip Rack](https://shop.opentrons.com/opentrons-20ul-filter-tips/)</br>

---

### Protocol Steps
1. For each column of samples, the [P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/) will pick up a set of tips, transfer the specified volume from column 1 of the reagent plate to the sample/destination plate, mix 5 times, then discard the tips.
2. If using the [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module), the thermal cycling steps will be performed on the OT-2. If not, the user will be prompted to move their plate to an off-deck thermal cycler.

### Process
1. Input your protocol parameters above.
2. Download your protocol.
3. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
657ee9
