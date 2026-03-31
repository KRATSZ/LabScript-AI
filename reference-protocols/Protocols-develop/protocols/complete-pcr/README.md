# Complete PCR Workflow with Thermocycler

### Author
[Opentrons](http://www.opentrons.com/)



## Categories
* PCR
    * Complete PCR Workflow

## Description
Part 1 of 2: Master Mix Assembly

Links:
* [Part 1: Master Mix Assembly](./pcr_prep_part_1)
* [Part 2: Master Mix Distribution and DNA Transfer](./pcr_prep_part_2)
* [Part 3: Thermocycler](./thermocycler)

This protocol allows your robot to create a master mix solution using any reagents stored in a 2 mL Eppendorf tube rack or a 2 mL screwcap tube rack. The master mix will be created in well A1 of the trough. The ingredient information will be provided as a CSV file. See Additional Notes for more details.

---

You will need:
* [4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [12-well Trough](https://www.usascientific.com/12-channel-automation-reservoir.aspx)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Select your pipettes.
2. Upload your master mix CSV.
3. Download your protocol.
4. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
7. Hit "Run".
8. Robot will transfer each reagent from its source to well A1 of trough in slot 3.


### Additional Notes
Slot 1: 2 mL Eppendorf Tube Rack
Slot 2: 2 mL Screwcap Tube Rack
Slot 3: 12-well Trough

---

![csv_layout](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/1473-acies-bio/CSV.png)

* The slot (1, 2) and well (A1 - D6) describe source location of the reagent
* You can add as many reagents as necessary
* Make sure you do not reuse the same well in the same slot
* Keep the headers

---

If you have any questions about this protocol, please contact protocols@opentrons.com.

###### Internal
OT-2 PCR Prep v2
