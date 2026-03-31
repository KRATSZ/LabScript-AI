# Equilibrium Dialysis with CSV

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol performs an equilibrium dialysis assay on the OT-2 using HTD plates. The HTD plate is mounted directly on the temperature module to achieve cooling, as well as the buffer. Backup buffer reservoirs are available on the deck, as well as waste reservoirs. A csv is uploaded to the protocol to gain information such as transfer volume, incubation time, and buffer volume. The OT-2 will only be accessing the bottom half of the wells for the duration of the protocol, so as to operate below the partition line. For detailed protocol steps, please see below.

Explanation of complex parameters below:
* `csv`: Here, you should upload a .csv file formatted in the following way, being sure to include the header line (note sample number should always be in multiples of 8 e.g. 8, 16, 24, 32, etc.):
```
N.º PROTEIN,VOLUME_EXCHANGE (ul) | VOLUME_RESERVOIR (ml) | TEMPERATURE_MODULE 1 (ºC) | TEMPERATURE_MODULE 2 (ºC) | TIME_PROTOCOL (min) | TIME_INCUBATE (min)
96,300,195,4,4,840,30
```
* `Initial volume of buffer reservoir`: Specify the volume inside each of the reservoirs in mL.
* `P300 Multi-Channel Mount`: Specify which mount (left or right) to host the P300 Multi-Channel pipette.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [NEST 1-Well Reservoirs, 195 mL](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/)
*[Opentrons 300µL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)
* [HTD Dialysis Plate](https://www.htdialysis.com/)

### Pipettes
* [P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4f7a64/Screen+Shot+2022-04-12+at+2.40.50+PM.png)


---

### Protocol Steps
1. Waste is removed from the bottom half of the wells in the plate up to the number of samples specified in the row of the csv. If all waste reservoirs are full, the protocol will automatically pause, prompting the user to empty waste reservoirs. Tips are exchanged between each column and disposed.
2. Using one column of tips, buffer is distributed from the reservoir on the temperature module to the bottom half of the wells in the plate, from the top of the well. Afterwards, the reservoir on the temperature module is replenished with back up buffer from slots 4, 5, and 6. If all of the back up buffer is depleted before the csv is completed, the protocol will automatically pause, prompting the user to replace buffer.
3. Protocol incubates according to the time specified in the csv. This also allows the replenished buffer to cool.

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
4f7a64
