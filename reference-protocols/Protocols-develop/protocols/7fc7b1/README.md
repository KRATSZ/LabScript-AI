# PCR Preparation Cherrypicking

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Featured
	* Cherrypicking

## Description
With this protocol, your robot can perform a custom PCR preparation using a P20-multi pipette.

This protocol allows you to choose which slots and plate (96 or 384 well) will be destination plates, and also gives the option to choose between a reservoir and 96 well plate as source plates for mastermix.

All available empty slots will be filled with tipracks, and the user will be prompted to refill the tipracks if all are emptied in the middle of the protocol.


Explanation of complex parameters below:
* `.csv file`: Upload a .csv file formatted in the [following way](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7fc7b1/7fc7b1_csv_template.csv), being sure to include the header line.
* `Mastermix Labware`: Specify whether you are using a 12-channel NEST 15mL reservoir or Greiner Bio-One 96-Well Plates 200µl well plate as the mastermix source. If you choose a 12-channel reservoir for mastermix, the mastermix should be filled in the first channel of the reservoir alone. If you choose a 96-well plate for mastermix, the mastermix should be filled in the first columns in as many columns as necessary. The protocol will automatically calculate when the second column should be acccessed for mastermix once the first column has run out of volume, then the third column, etc.
* `Mastermix Plate Slot`: Specify which slot the mastermix will be on the deck.
* `Mastermix Volume Loaded in Source`: Specify the volume of mastermix per column in ul.
* `Mastermix Starting Column`: Specify the column in which populated mastermix columns start.
* `DNA Volume`: Specify the DNA volume (in ul) to which mastermix will be added.
* `Transfer Scheme`: Specify whether the transfer scheme will be multi-dispense or single dispense (distribution vs 1-1 transfer).
* `P20-multi GEN2 mount`: Specify which mount (left or right) the P20 Multi-GEN2 mount will be.







---
### Labware
* [Greiner Bio-One 96-Well Plates 200µl #652290](https://shop.gbo.com/pt/brazil/products/bioscience/biologia-molecular/pcr-microplates/bs-96-well-polypropylene-microplates/652290.html)
* [Sarstedt 384-Well Plates 40µl #72.1984.202](https://www.sarstedt.com/en/products/laboratory/pcr-molecular-biology/pcr-plates/product/72.1984.202/)
* [Nest 12-Well Reservoir 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 20µl tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Pipettes
* [Opentrons P20 GEN2 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)


---

### Deck Setup
Example Deck Layout:
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7fc7b1/Screen+Shot+2021-04-29+at+11.13.25+AM.png)

---

### Protocol Steps
Example steps for Nest 12 well reservoir and multi-dispense.

1. Aspirate user-specified volume of mastermix from first well on NEST resevoir.
2. Dispense user-specified volume of mastermix into Sarstedt 384 well plate in user-specified well.
3. Process is repeated for each row in CSV file.

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
7fc7b1
