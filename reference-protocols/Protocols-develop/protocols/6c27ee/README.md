# Custom CSV Transfer

### Author
[Opentrons](http://www.opentrons.com/)



## Categories
* Sample Prep
    * Cherrypicking

## Description
This protocol performs cherrypicking from source to target plates as specified in an input CSV file. The protocol parses the CSV for slots to load the source and target plates. Only non-zero volume transfers are carried out for efficiency, and the user is prompted to refill tipracks if necessary.</br>
</br>

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [P50 Single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549077021)
* [P300 8-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549109789)
* [Opentrons 300µl Pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Corning 96-Well Plate, Flat 360µL](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [USA Scientific 12-Well Reservoir, 22mL](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
**Slot 1**: [Opentrons 300µl Pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) (for P50 Single-Channel)</br>
</br>
**Slot 2**: [Corning 96-Well Plate, Flat 360µL](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate) (ELISA plate A)</br>
</br>
**Slot 3**: [USA Scientific 12-Well Reservoir, 22mL](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir)</br>
</br>
**Slot 4**: [Opentrons 300µl Pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) (for P300 8-Channel)</br>
</br>
**Slot 5**: [Corning 96-Well Plate, Flat 360µL](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate) (ELISA plate B)</br>
</br>
**Slot 6**: [Corning 96-Well Plate, Flat 360µL](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate) (1st Dilution Plate)</br>
</br>
**Slot 7**: Opentrons 300µl Pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) (for P300 8-Channel)</br>
</br>
**Slot 8**: [Corning 96-Well Plate, Flat 360µL](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate) (ELISA plate C)</br>
</br>
**Slot 9**: [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) containing 2mL Tubes</br>
</br>
**Slot 10**: [Corning 96-Well Plate, Flat 360µL](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate) (2nd Dilution Plate)</br>
</br>
**Slot 11**: [Corning 96-Well Plate, Flat 360µL](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate) (ELISA plate D)</br>
</br>

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Upload your CSV.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact protocols@opentrons.com.

###### Internal
6c27ee
