# mRNA Encapsulation

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol uses single-channel P300 and P1000 pipettes to perform plate filling steps with 1-5 input samples for each of up to 4 test plates to be filled using the deck layout and source and destination locations displayed in the attached .json file [deck map and source and destination wells](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/37ffa5/Based_on_zoom_conf.json) (note: the attached json file is for visualization of the deck layout and location of source and destination wells using [Opentrons Protocol Designer](https://designer.opentrons.com/), it is not a fully-developed .json protocol to be run on the OT-2, the pipetting technique and transfer order have been modified for run time reasons). All transfers required for set up of the first test plate are completed prior to the start of the next test plate to minimize the per-plate run time. The user can pause the robot in order to remove completed plates during the run. Multi pre-air gaps with multiple aspirations are performed to enable repeat dispenses at the top of the well without need for blowout, tip touch or tip drops. User-determined parameters are available to specify the number of samples in each row of the tube rack.


---


### Labware
* [Opentrons Tips for the P300 and P1000] (https://shop.opentrons.com)
* [Opentrons 4-in-1 Tuberack, Nest 1.5 mL Snap Cap Tubes, Corning 360 uL Flat 96-well Plate] (https://shop.opentrons.com)


### Pipettes
* Opentrons single-channel P300 and P1000 Gen2 Pipettes (https://shop.opentrons.com/pipettes/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/37ffa5/screenshot-deck.png)
</br>
</br>
**Slot 1**: Opentrons 1000 uL Tips </br>
**Slot 2**: Opentrons 300 uL Tips </br>
**Slot 3**: Test Plate 1 (Corning 360 uL Flat 96-Well Plate) </br>
**Slot 4**: Sample Plate (Corning 360 uL Flat 96-Well Plate) </br>
**Slot 5**: Test Plate 4 (Corning 360 uL Flat 96-Well Plate) </br>
**Slot 6**: Test Plate 2 (Corning 360 uL Flat 96-Well Plate) </br>
**Slot 7**: 25 ug/mL Sample Stock (Opentrons 24-Tube Rack holding 1.5 mL Nest SnapCap Tubes) </br>
![tuberack](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/37ffa5/screenshot-tuberack.png)
</br>
</br>
**Slot 8**: Buffer Reservoir (USA Scientific 22 mL 12 Well Reservoir) </br>
![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/37ffa5/screenshot-reservoir.png)
</br>
</br>
**Slot 9**: Test Plate 3 (Corning 360 uL Flat 96-Well Plate) </br>

---

### Protocol Steps
1. The protocol will alert the user to ensure buffers are present in the reservoir in sufficient volume.
2. The p1000 is used to repeat top-dispense PBS (without need for blowout or tip touch) to the first two rows of the sample plate (multi pre-air gap is used).
3. The p300 single is used to repeat top-dispense sample (without need for blowout or tip touch) from row A of the tube rack to the first two rows of the sample plate (multi pre-air gap is used).
4. The p300 single and p1000 are used to repeat top-dispense TE (without need for blowout or tip touch) to the first test plate (multi pre-air gap is used).
5. The p1000 and p300 single are used to repeat top-dispense TE Triton to the first test plate (multi pre-air gap is used).
6. The p300 single is used to repeat top-dispense sample (without need for blowout or tip touch) from the sample plate to the first test plate (multi pre-air gap is used).
7. The p1000 is used to repeat top-dispense mRNA stock to the first test plate.
8. The p300 single is used to mix and prepare a dilution series of the mRNA stock in the first test plate.
9. Steps 1-8 are repeated for samples and mRNA stock in tube rack rows B, C and D and the corresponding test plates.


### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
37ffa5
