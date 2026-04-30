# ELISA Protocol 2/3: Antibody Addition

### Author
[Opentrons](http://www.opentrons.com/)



## Categories
* Proteins & Proteomics
    * ELISA

## Description
Links:
* [Part 1: Dilution](./1464-natrix-separations-inc-milliporesigma-part1)
* [Part 2-1: Antibody Addition](./1464-natrix-separations-inc-milliporesigma-part2)
* [Part 2-2: Substrate and Stop Solution Addition](1464-natrix-separations-inc-milliporesigma-part3)

This is the second part of a ELISA protocol: Antibody Addition. The robot will first add Enzyme Conjugate Reagent to all of the columns required in the output plate in slot 9. Water, diluent, and HCP standards, and diluted samples will be transferred to the output plate in duplicate. User will need to upload the same CSV file used in part 1 of the protocol. See Additional Notes in Part 1 for more details on the CSV requirements.

Download full protocol details [here](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/1464-natrix-separations-inc-milliporesigma/NEW_ELISA_protocol.xlsx).

---

You will need:
* P300 Multi-channel Pipette
* P300 Single-channel Pipette
* [Opentrons Tube Racks (2 mL Eppendorf)](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons Tube Rack (15 + 50 mL)](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [2 mL 96-deep well Plate](https://www.usascientific.com/2ml-deep96-well-plateone-bulk.aspx)
* 96-well Plate
* 12-row Trough
* 300 uL Tip Racks

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Select the number of standards you are using.
2. Upload the same concentration CSV you uploaded to part 1 of the protocol.
3. Download your protocol.
4. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
7. Hit "Run".


### Additional Notes
Tube Rack setup: (slot 4)
* DI Water: A1
* Diluent: A2
* HCP Standards: A3-B2 if number of standards is 6, A3-B4 if 8
* Samples: B3-(D6) if number of standards is 6, B5-(D6) if 8
You will need to shift the locations of the samples based on the number of standards you have each run. This configuration must be consistent of that of part 1.

---

If you have any questions about this protocol, please contact protocols@opentrons.com.

###### Internal
AwOUI09G
1464
