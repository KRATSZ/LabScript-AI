# Mass Spec Sample Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Mass Spec

## Description

This custom protocol performs 2 parts of a mass spec sample prep:
1. Precipitate supernatant transfer
2. Mobile phase A reconstitution

The user is prompted to refill the tuberacks for as many samples as specified. The protocol begins with samples 1-24 loaded in the tuberack on slot 1.

---

### Labware
* [Opentrons 4-in-1 Tuberack Set](https://shop.opentrons.com/4-in-1-tube-rack-set/) with 4x6 adapter for [Eppendorf 1.5 mL Safe-Lock Snapcap Tubes](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Tubes-44515/Eppendorf-Safe-Lock-Tubes-PF-8863.html)
* [Opentrons 1000µL Tips](https://shop.opentrons.com/opentrons-1000-l-tips/)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)

### Pipettes
* [Opentrons P1000 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/64c54a/deck.png)

---

### Protocol Steps
1. 900 uL supernatant is transferred to a new Eppendorf tube (without disturbing the pellet).
2. User is prompted to dry all samples to with a N2 dryer or SpeedVac with no temp
3. The dry extracts are reconstituted with 100 µL mobile phase A.

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
64c54a
