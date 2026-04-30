# Custom Serial Dilution for Protein Quantification

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Serial Dilution

## Description
This protocol uses a multi-channel P300 and single-channel P20 pipette to perform custom serial dilution of up to 48 input protein samples. There are six dilution schemes (defined below) which differ in diluent volume, sample volume, number of mix repeats, fold dilution and number of dilution points. An input csv file assigns a dilution scheme and a sample number to each sample (sample numbers 1-48 in column-wise order spanning two 24-tube racks). Samples using the same dilution scheme are assigned (up to 8 at a time) to a block of four consecutive dilution plate columns. The p300 will pick up a number of tips corresponding to the current number of samples (up to 8) and fill two to four dilution plate columns (depending on the assigned dilution scheme) with dilution buffer. The p20 will add sample to the filled wells of the first column. The p300 will then perform serial dilution steps (mixing and transfer to the next column). User-specified parameters are available to indicate the labware to be used for the diluent reservoir, and the necessary amount of deadvolume (small amount of inaccessible liquid in the bottom of the reservoir) for that reservoir. A downloadable output file (see instructions below) will be generated which indicates the dilution plate destination well for each input sample.

Links:
* [example input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/058124/input_csv.csv)</br>

![dilution schemes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/058124/screenshot-dilutionparameters.png)</br>
![input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/058124/screenshot-inputfile.png)</br>
![output csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/058124/screenshot-outputfile.png)</br>

---


### Labware
* [Opentrons Filter Tips for the P20 and P300] (https://shop.opentrons.com)
* [Opentrons 24-Tube Racks] (https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Nest 1.5 mL Snap Cap Tubes](https://shop.opentrons.com/nest-1-5-ml-microcentrifuge-tube/)
* [Nest 96 Deep Well Plates 2 mL] (https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [Axygen 90 mL Reservoir] (https://labware.opentrons.com/axygen_1_reservoir_90ml/)



### Pipettes
* Opentrons single-channel P20 and multi-channel P300 Gen2 Pipettes (https://shop.opentrons.com/pipettes/)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/058124/screenshot-deck.png)
</br>
</br>
**Slots 1,4**: Opentrons 24-Tube Rack with 1.5 mL Snap Cap Tubes (up to 48 Protein Samples) </br>
**Slots 2,3,5,6**: Nest 96 Deep Well 2 mL Plates (up to 4 Dilution Plates) </br>
**Slot 10**: Opentrons 20 uL filter tips </br>
**Slot 11**: Opentrons 200 uL filter tips </br>




---

### Protocol Steps
1. For each dilution scheme - the protocol will display the number of sample columns (containing up to 8 samples) to be diluted.
2. The protocol will pause to alert the user to ensure sufficient volume of diluent is in the reservoir.
3. The protocol will display the current dilution scheme, all sample numbers assigned to that scheme, the current samples being processed, the current dilution plate destination.
4. The p300 multi will pick up a number of tips corresponding to the number of current samples being processed (up to 8).
5. The p300 multi will transfer diluent from the reservoir to the destination columns for the current samples.
6. The p20 single will transfer each current sample to a well in the 1st destination column.
7. The p300 multi will perform serial dilution steps (mix and transfer to the next column).
8. The protocol will generate an output file which identifies the destination well in the dilution plates for each input sample.
9. The output file can be downloaded to the user's computer when the run is finished. Use the Opentrons app to locate and download the output file (Devices tab, find your robot, with the three dots in the upper right corner - Robot Settings, use the Advanced tab, click Launch Juypter Notebook to open web browser, where you can view and download the output file).


### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck and run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
058124
