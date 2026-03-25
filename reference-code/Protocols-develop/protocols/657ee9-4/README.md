# Oncomine Focus Assay - Pt 4: Purify Library + Elution

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Oncomine Focus Assay

## Description
This is the fourth (and last) part in a multi-part protocol designed to automate the Oncomine Focus Assay. For a detailed description of the manual protocol, please see [this resource.](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2022-01-27/kk23ns4/MAN0015819_Part1_OFAv1S5FTLibraryPrep_UG.pdf)

In this protocol, the OT-2 automates the 'Purify The Library' and the 'Elute The Library' portions of the protocol. Using the complex parameters described below, the user can specify which, if any, modules they are using and select from different options pertaining to RNA/cDNA and DNA (**Columns with Samples**).

**Update**: Protocol was updated to accommodate single column input.

Explanation of complex parameters below:
* **Columns with Samples**: Specify which columns should we receive the FuPa reagent. Column numbers should be separated by a comma (,).
* **P300-Multi Mount**: Select which mount the [P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/) is attached to.  

---

### Modules
[Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)


### Labware
* [NEST 96-Well PCR Plates](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/opentrons-200ul-filter-tips/)



### Pipettes
* [P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Reagents
* [Oncomine Focus Assay](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2022-01-27/kk23ns4/MAN0015819_Part1_OFAv1S5FTLibraryPrep_UG.pdf)


---

### Deck Setup
**Slot 1**: [[NEST 96-Well PCR Plates](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/) containing samples on the [Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck).</br>
</br>
**Slot 2**: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/) containing reagents. </br>
</br>
**Slot 3**: [NEST 96-Well PCR Plates](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/), empty for elutes.</br>
</br>
**Slot 4**: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/opentrons-200ul-filter-tips/)</br>
</br>
**Slot 5**: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/opentrons-200ul-filter-tips/)</br>
</br>

### Reagent Setup
[NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/) in **Slot 2**:
* **Column 1**: Agencout AMPure XP Reagent
* **Column 3**: 70% Fresh Ethanol
* **Column 5**: Low TE
* **Column 11**: Empty (Liquid Waste)


---

### Protocol Steps
1. For each column of samples, the [P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/) will pick up a set of tips, transfer 45µL of Agencout AMPure XP Reagent from Column 1 of the [NEST 12-Well Reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/) to the plate containing samples, mix 5 times, then discard the tips.
2. There will be a 5 minute incubation period ([Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) disengaged).
3. There will be a 2 minute incubation period ([Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) engaged).
4. [Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) will disengage.
5. For each column of sample, the [P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/) will pick up a set of tips, transfer 75µL supernatant to Column 11 of the [NEST 12-Well Reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/), then discard tips.
6. For each column of samples, the [P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/) will pick up a set of tips, transfer 150µL of Ethanol from Column 3 of the [NEST 12-Well Reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/) to the plate containing samples, mix 5 times, then discard the tips.
7. There will be a 2 minute incubation period ([Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) engaged).
8. For each column of sample, the [P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/) will pick up a set of tips, transfer 150µL supernatant to Column 11 of the [NEST 12-Well Reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/), then discard tips.
9. [Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) will disengage.
10. Steps 5-9 will repeat (2nd wash).
11. There will be a 2 minute incubation period ([Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) disengaged).
12. For each column of samples, the [P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/) will pick up a set of tips, transfer 50µL of Low TE from Column 5 of the [NEST 12-Well Reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/) to the plate containing samples, mix 5 times, then discard the tips.
13. There will be a 2 minute incubation period ([Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) disengaged).
14. There will be a 2 minute incubation period ([Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) engaged).
15. For each column of sample, the [P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/) will pick up a set of tips, transfer 50µL supernatant from the column to the next empty column of the empty [NEST 96-Well PCR Plates](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/) in Slot 3, then discard tips.


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
657ee9-4
