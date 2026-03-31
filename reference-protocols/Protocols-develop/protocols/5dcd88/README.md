# nCoV-2019 Lo Cost protocol

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol preps a 96 well plate with barcoded, amplified sample. Ultimately, barcoded samples are pooled into a final 1.5mL tube.

Water and mastermix are added to samples, after which an incubation period follows with subsequent temperature changes. User will load a new PCR plate onto the temperature module for the final sample collecting. User will also pull the sample plate from the deck after the second barcode mastermix is added to barcode samples. After another incubation period with subsequent temperature changes, samples are pooled. The protocol will automatically pause for all steps requiring user intervention.


Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples for this run
* `P20 Multi-Channel Mount`: Specify which mount (left or right) to host the P20 Multi-Channel Pipette.
* `Park Tips?`: Specify whether or not you would like to park tips for this run
* `P300 Multi-Channel Mount`: Specify which mount (left or right) to host the P300 Multi-Channel

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [NEST 100ul PCR Plate Full Skirt](https://shop.opentrons.com/collections/lab-plates?_gl=1*1qe5wkp*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTYzNTQ2NTkzNy40ODMuMS4xNjM1NDY3NTI0LjA.&_ga=2.122884237.745121471.1635259113-1365106149.1621361358)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 12 Well Reservoir 195mL](https://shop.opentrons.com/collections/reservoirs)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)



### Pipettes
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5dcd88/Screen+Shot+2021-11-03+at+5.09.47+PM.png)



---

### Protocol Steps
1. This section should consist of a numerical outline of the protocol steps, somewhat analogous to the steps outlined by the user in their custom protocol submission.
2. example step: Samples are transferred from the source tuberacks on slots 1-2 to the PCR plate on slot 3, down columns and then across rows.
3. example step: Waste is removed from each sample on the magnetic module, ensuring the bead pellets are not contacted by the pipette tips.

### Process
1. One to one well transfer between plate 1 into plate 2, 25ul. Mix 35ul, 10 times.
2. Add water in new 96 well (deck slot 3). 5 ul from slot 1 to slot 3. Mix 35ul, 20 times.
3. 6.7ul mastermix (single 1.5 tube) 8-channel as a single channel.
4. One tip multi dispense 96 well plate on temperature.
5. 8 channel again 3.3ul mixing 10 repetitions 7.5 ul.
6. Incubate at R/T for 15 min.
7. Incubate at 65°C for 15 min.
8. Down to 4C for 1 minute.
9. PROTOCOL PAUSE - protocol will prompt user what to do.
10. 7.75ul of barcode in new plate NEST (100ul pcr).
11. Adding 7.75 ul of barcode from a tube into clean 96 aluminum block on temperature module, one tip multi dispense.
12. Pause to let user add 1.25ul of barcode.
13. Final plate of protocol one is the end prep reaction, add 1ul, mix 7.5ul for 10 times.
14. Incubate at R/T for 30 min.
15. Incubate at 65°C for 10 min.
16. Incubate 4C for 1 minute.
17. Pool 2.5ul of each well into new 1.5 tube.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
5dcd88
