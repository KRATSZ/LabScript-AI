# Custom Drug Dilution Assay

### Author
[Opentrons](http://www.opentrons.com/)



## Categories
* Sample Prep
    * Serial Dilution

## Description
This protocol is an updated version of a drug dilution protocol designed with Protocol Designer.</br>
</br>
In this protocol, the p300-multi channel pipette (GEN1) is used to transfer 100µL media to all of the columns of the three dilution plates (10uM, 1uM, and 0.1uM). When transferring the media, the same tips (column 1) will be used for all transfers, but after every four transfers, the pipette will return the tips to the tiprack and pick up them up again to ensure a good seal with the tips.</br>
After the media is added, the p10-multi channel pipette is used for the dilutions, transferring 10µL from a stock plate in slot 10, to the first dilution plate and so on... (using the same set of tip for each column of dilutions).</br>
Finally, the p300-multi will be used again, this time transferring 100µL from the reservoir in slot 11 to the three dilution plates. These transfers will follow the same pattern for tip usage as the earlier transfer with the p300-multi, but instead use the tips from column 2.</br>
</br>

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* P300 Multi-Channel Pipette (GEN1)
* P10 Multi-Channel Pipette
* [Opentrons 300µl Pipette Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 10µL Pipette Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [Axygen 1-Well Reservoir, 90mL](https://labware.opentrons.com/axygen_1_reservoir_90ml/)
* [Corning 96-Well Plate, 360µL Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
**Slot 1**: [Corning 96-Well Plate](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate) (Drug Dilution 0.1µM)</br>
</br>
**Slot 2**: [Opentrons 300µl Pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)</br>
</br>
**Slot 4**: [Corning 96-Well Plate](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate) (Drug Dilution 1µM)</br>
</br>
**Slot 5**: [Opentrons 10µL Pipette Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)</br>
</br>
**Slot 7**: [Corning 96-Well Plate](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate) (Drug Dilution 10µM)</br>
</br>
**Slot 8**: [Axygen 1-Well Reservoir](https://labware.opentrons.com/axygen_1_reservoir_90ml/) (containing Media for 1st transfer)</br>
</br>
**Slot 10**: [Corning 96-Well Plate](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate) (Drug Stock)</br>
</br>
**Slot 11**: [Axygen 1-Well Reservoir](https://labware.opentrons.com/axygen_1_reservoir_90ml/) (containing Cells for 2nd transfer)</br>
</br>

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Specify your parameters on this page.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact protocols@opentrons.com.

###### Internal
3662e6
