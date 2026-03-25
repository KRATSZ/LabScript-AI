# CSV Cherrypicking APIv2

### Author
[Opentrons](http://www.opentrons.com/)



## Categories
* Sample Prep
    * Cherrypicking

## Description
This protocol performs cherrypicking from source to target plates as specified in an input CSV file. The protocol parses the CSV for slots to load the source and target plates. Only non-zero volume transfers are carried out for efficiency, and the user is prompted to refill tipracks if necessary.</br>
</br>
**This protocol is an update of this [APIv1 protocol](https://protocol-delivery.protocols.opentrons.com/protocol/1617).**

---

You will need:
* [P10 Single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [P50 Single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549077021)
* [P300 Single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549109789)
* [10µl Pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [300µl Pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Biorad Hard-Shell 96-Well PCR Plates # HSP9601](http://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Upload your CSV, and input your source and destination plate types, and pipette combination.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".
7. A transfer is performed for each set of source plate and well, target plate and well, and volume. New tips are used for each transfer, and the user is prompted to replace tip racks once they are used. 0µl transfers are skipped for efficiency.

### Additional Notes
If you have any questions about this protocol, please contact protocols@opentrons.com.

###### Internal
44981c
