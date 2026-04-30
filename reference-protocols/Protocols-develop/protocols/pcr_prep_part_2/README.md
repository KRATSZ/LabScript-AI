# OT-2 PCR Prep 2/2: Master Mix Distribution and DNA Transfer

### Author
[Opentrons (verified)](https://opentrons.com/)


## Categories
* PCR
    * PCR Prep

## Description
Part 2 of 2: Master Mix Distribution and DNA Transfer

Links:
* [Part 1: Master Mix Assembly](./pcr_prep_part_1)
* [Part 2: Master Mix Distribution and DNA Transfer](./pcr_prep_part_2)


This protocol allows your robot to distribute a master mix solution from well A1 of a trough to PCR strips. Robot will then transfer DNA samples to the master mix solution.

---

You will need:
* [12-channel reservoir](https://www.usascientific.com/12-channel-automation-reservoir.aspx)
* [96-well PCR plate](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the number of samples you are processing.
2. Select your pipettes.
3. Input the desired master mix and DNA volume in each well.
4. Download your protocol.
5. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
6. Set up your deck according to the deck map.
7. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
8. Hit "Run".
9. Robot will distribute master mix solution from trough to PCR strips in slot 2.
10. Robot will transfer DNA from PCR strips in slot 1 to those in slot 2.

### Additional Notes
Slot 1: PCR plate with DNA samples
Slot 2: Empty PCR plate
Slot 3: 12-channel reservoir with master mix solution in well A1

Please reference our [Application Note](https://opentrons-protocol-library-website.s3.amazonaws.com/Technical+Notes/Thermocycler+PCR+Application+Note.pdf) for more information about the expected output of this protocol.

---

If you have any questions about this protocol, please contact protocols@opentrons.com.

###### Internal
OT-2 PCR Prep v2
