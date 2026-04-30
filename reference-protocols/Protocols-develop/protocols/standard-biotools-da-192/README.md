# Standard Biotools Dynamic Array 192.24: Load 4 uL

### Author
[Standard BioTools](https://www.standardbio.com/)

### Partner
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* Standard BioTools


## Description
![Standard BioTools Logo](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/standard-biotools/standard-bio-logo-200-TM.jpg)
</br>
This protocol transfers 4 µL of samples and assays from 96-well plates to the Standard BioTools 192.24 IFC (Integrated Fluidic Circuit)</br>
![Standard BioTools 192](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/standard-biotools/Opentrons_Figs_192.jpg)
</br>
**Preparation**:</br>
Before beginning the protocol on the OT-2, perform the following preparation steps:
1. Prepare the Samples, the Assays, and the IFC Referring as described in one of the following workflows from the Standard BioTools X9 User Guide:
- Gene Expression Using the 192.24 IFC with TaqMan Assays
- Genotyping Using the 192.24 IFC with SNP Type Assays
- Genotyping Using the 192.24 IFC with TaqMan Assays
2. Prepare two Sample Plates by transferring 6 µL of sample to all wells of two separate 96-well plates
3. Prepare an Assay Plate by transferring 6 µL of assay to 24 wells of a 96-well plate
4. *NOTE*: All wells (indicated below in blue) must have liquid
5. Centrifuge the Sample and Assay plates to ensure liquids are at the bottom of the wells
6. Prepare the 192.24 IFC:
- Add control line fluid to the accumulators according to the workflow selected in step 1 (Indicated above by red arrows)
- Remove the protective film from the bottom of the IFC
7. Prepare a 1.5 mL tube with 170 µL Standard Biotools Actuation Fluid (green)
8. Prepare a 1.5 mL tube with 370 µL Standard Biotools Pressure Fluid (red)



### Labware
* Standard BioTools 192.24 Dynamic Array IFC
* [Opentrons 96 Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [NEST 96-Well PCR Plate, 100µL](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* VWR 96 Well Plate 200 µL PCR (89218-290)
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* Eppendorf 1.5 mL Safe-Lock Snapcap
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/)


### Pipettes
* [Opentrons P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/standard-biotools/Opentrons+Protocols+Figs_192.24+Layout.jpg)


### Protocol Steps
1. Transfer Actuation Fluid to IFC
2. Transfer Pressure Fluid to IFC
3. Transfer assays to IFC
4. Transfer samples to IFC

</br>
*NOTE*: Mapping from the sample / assay plates to the IFC matches the mapping defined by the workflow selected in Preparation: Step 1



### Process
1. Download your protocol and unzip if needed.
2. Import your labware file(s) (.json extension) to the [OT App](https://opentrons.com/ot-app) in the `labware` tab, if needed.
3. Import your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/s/article/How-positional-calibration-works-on-the-OT-2).
6. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
standard-biotools-da-192
