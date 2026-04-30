# Dispense PCR Master Mix (plates)

### Author
[REM Analytics](https://www.remanalytics.ch/)



## Categories
* PCR Prep
	

## Description
Protocol to dispense master mix (with or without DNA) in PCR plates. The current protocol dispenses only one mix per 
plate. You input the number of plates that you'd like to
prepare and the protocol pauses after preparing each plate. This gives you the opportunity to wait for the previous 
plate to finish, prepare the following master mix etc. The protocol will tell you which trough you need to pour the mix
into for the following plate.

Explanation of parameters below:
* `Master Mix Source`: Do you have one master mix for the whole plate (Reservoir) or one for each row (Plate). NB the
Deck Setup diagram shows both the Plate and Reservoir (troughs), you only need to put the one
you require in place.
* `Number of Plates`: The total number of plates you'd like to prepare (one master mix needs to be prepared for each 
plate)
* `Starting Trough`: The first trough you'd like to pour the master mix into (e.g. if some troughs have already been
used). NB the subsequent troughs will be used for the following plates so they also need to be free. Make sure
that Number of Plates is *not* greater than the number of available troughs, if so use a new reservoir plate.
* `Volume to dispense (uL)`: Typically 9 (without DNA in mix) or 10 (with DNA in mix).
* `Touch Tip on the...`: Which side should the tip touch the well on (the opposite side to which you touched the tip
when adding the DNA (if applicable)) 


---


### Labware

* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml/)
* [Shallow Well Plate 200 uL (x2)](96w_pcr_plate2.json)

### Pipettes
* [P10 8-Channel Electronic Pipette](https://docs.opentrons.com/v1/pipettes.html)

### Reagents
* Pre-prepared Master Mixes (depending on the dispense volume, the protocol will tell you the minimum Master Mix
volume you need to add to the trough).
---

### Deck Setup
* After each plate is prepared, the protocol pauses, the plate must be removed and the following plate must be placed
  in the same slot.
  ![deck layout](https://raw.githubusercontent.com/jamiesone/images/main/Screenshot%20from%202021-12-03%2017-14-49.png)

---

### Protocol Steps
1. Pause: check the plate/master mix are in place.
2. Pick up tips and transfer master mix to all columns of the plate in slot 5.
3. Drop tips in waste bin.
4. Pause until ready to prepare the following plate.

### Process
1. Input the parameters (volume, no. of plates etc.) in the fields above.
2. Download your protocol and unzip if needed.
3. Once connected to the robot, upload your protocol file (.py extension) to the Opentrons software in the `Protocol` tab.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Click 'Run'.


