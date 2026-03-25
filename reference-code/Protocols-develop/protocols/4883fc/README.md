# Normalization

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description
![Normalization Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/normalization/normalization_example.png)

Concentration normalization is a key component of many genomic and proteomic applications, such as NGS library prep. With this protocol, you can easily normalize the concentrations of samples in a 96-well plate from either 1.5ml snapcap tubes, or another 96-well plate. The transfers should be specified as an input .csv file formatted as shown here:

```
Sample number,Slot no number,Source well,Destination well,Start Concentration (ug/uL) Source,Final Concentraion (ug/ml) Destination,Sample volume (uL),Diluent Volume(ul),Total Volume(ul) Destination
1,4,A1,A1,5,2,40,60,100.0
2,4,C1,B1,3,2,67,33,100.0
3,4,D1,C1,10,2,20,80,100.0
4,4,E3,D1,20,2,10,90,100.0
```

You can also download and edit [this template](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4883fc/example.xlsx). Be sure to export the `.xlsx` format to `.csv` format before inputting as the `input .csv file` below!

---

### Labware
* [NEST 96 Well Plate 100 µL PCR Full Skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [NEST 1.5 mL Microcentrifuge Tube](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* [Opentrons pipette tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 12 Well Reservoir 15 mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)

### Pipettes
* [Opentrons Single-Channel Electronic Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

---

### Deck Setup
* if sources are arranged in 1.5ml tubes:  
![tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4883fc/tuberack.png)

* if sources are arranged in a 96-well plate:  
![plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4883fc/plate.png)

### Reagent Setup
* NEST 12-channel reservoir (slot 9): diluent (10000µl per channel, dependent on number of normalizations)

### Protocol Steps
1. Diluent is transferred in the proper amounts to each destination well of the end PCR plate using 1 tip for the entire set of transfers.
2. The first sample is transferred to its specified destination well with pre-added diluent, the well is mixed 3x. After dispense, a blowout and touch tip are performed. The tip is then dropped.
3. Step 2 is repeated for as many samples as specified in the .csv file.

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
4883fc
