# Custom Normalization from a CSV File

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Normalization

## Description
This protocol uses single-channel P20 and P300 pipettes to normalize DNA concentrations of up to 96 input samples based on user input (input DNA sample concentration, target concentration, target volume) provided by csv file upload (see example file below). Intermediate dilutions are prepared as needed. A downloadable output file is generated to record calculated fold dilution, volume of sample and water transferred, if a sample was processed (or skipped due to insufficient input DNA concentration), and if an intermediate dilution was required.

Links:
* [example input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04f310/normalization_example_input.csv)</br>

![input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04f310/screenshot-example_input_csv.png)</br>

Values for CSV file input:
* sample_id
* dna_conc_initial (ng/ul)
* dna_conc_target (ng/ul) 5-40 ng/uL
* volume_target (ul) 30-100 uL

![output csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04f310/screenshot-example_output_csv.png)</br>

Additional Calculated Values in CSV file output:
* fold dilution
* sample_transfer (ul)
* water_transfer (ul)
* processed (0 - sample was skipped, 1 - sample was processed)
* intermediate_dilution (0 - intermediate dilution not required, 1 - intermediate dilution required)

---


### Labware
* [Opentrons Filter Tips for the P20 and P300] (https://shop.opentrons.com)
* [Opentrons 10-Tube Rack] (https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [BioRad 200 uL PCR Plate] (https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [NEST 96 Deep Well Plate 2 mL] (https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate)
* [Agilent 290 mL Reservoir] (https://labware.opentrons.com/agilent_1_reservoir_290ml?category=reservoir)



### Pipettes
* Opentrons single-channel P20 and single-channel P300 Gen2 Pipettes (https://shop.opentrons.com/pipettes/)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04f310/screenshot-deck.png)
</br>
</br>
**Slot 1**: Opentrons 10-Tube Rack with Falcon 50 mL Conical Tube (containing 40 mL water) </br>
**Slot 5**: BioRad 200 uL PCR Plate (output plate) </br>
**Slot 8**: BioRad 200 uL PCR Plate (intermediate dilution plate) </br>
**Slot 9**: Agilent 290 mL Reservoir (filled with 10 percent diluted bleach) </br>
**Slot 11**: NEST 96 Deep Well Plate 2 mL (containing input DNA samples >= 50 uL) </br>
**Slot 7**: Opentrons 20 uL filter tips </br>
**Slot 10**: Opentrons 200 uL filter tips </br>


---

### Protocol Steps
1. The protocol will calculate the fold dilution and volume of water and sample to be transferred to the output plate and will determine and record if an intermediate dilution is required (if calculated sample transfer volume is < 2 uL) or if a sample must be skipped (if calculated sample transfer volume is greater than the available input sample volume of 30 uL).
2. The p20 single and p300 single will transfer water to output plate wells and return tips for reuse.
3. The p20 single and p300 single will transfer sample to output plate wells. If required, an intermediate dilution (10X dilution - 2 uL sample + 18 uL water) will be prepared, mixed and used as the source of sample transfer to the output plate. Each tip will be rinsed 1X in 10 percent diluted bleach prior to being dropped in the trash bin.
4. The protocol will generate an output file which can be downloaded to the user's computer when the run is finished. Use the Opentrons app to locate and download the file (Devices tab, find your robot, with the three dots in the upper right corner - Robot Settings, use the Advanced tab, click Launch Juypter Notebook to open web browser, where you can view and download the output file).



### Process
1. Input your csv file using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
04f310
