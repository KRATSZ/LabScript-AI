# Cherrypicking


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Cherrypicking


## Description
This protocol performs a custom cherrypicking for any number of source and destination plates using a P20 single-channel pipette. An output file mapping each sample ID, source plate ID, and destination plate ID is output for each run.

The input .csv file should be formatted as follows **including header line**

```
,clone ID,0ur plate ID,Source Labware,Source Slot,Source Well,Source Aspiration Height Above Bottom (in mm),Dest Labware,Dest Slot,Dest. Plate ID,Dest Well,Volume (in ul)
n1,CL-1418591,1,biorad_96_wellplate_200ul_pcr,2,B06,1,biorad_96_wellplate_200ul_pcr,11,RAILPB03,A01,15
n2,CL-1418640,1,biorad_96_wellplate_200ul_pcr,2,D12,1,biorad_96_wellplate_200ul_pcr,11,RAILPB03,A02,15
n3,CL-1418621,1,biorad_96_wellplate_200ul_pcr,2,H09,1,biorad_96_wellplate_200ul_pcr,11,RAILPB03,A03,15
n4,CL-1418715,2,biorad_96_wellplate_200ul_pcr,3,H09,1,biorad_96_wellplate_200ul_pcr,11,RAILPB03,A04,15
n5,CL-1418738,3,biorad_96_wellplate_200ul_pcr,4,A01,1,biorad_96_wellplate_200ul_pcr,11,RAILPB03,A05,15
n6,CL-1418818,3,biorad_96_wellplate_200ul_pcr,4,A11,1,biorad_96_wellplate_200ul_pcr,11,RAILPB03,A06,15
n7,CL-1418744,3,biorad_96_wellplate_200ul_pcr,4,G01,1,biorad_96_wellplate_200ul_pcr,11,RAILPB03,A07,15
n8,CL-1418866,4,biorad_96_wellplate_200ul_pcr,5,C05,1,biorad_96_wellplate_200ul_pcr,11,RAILPB03,A08,15
n9,CL-1418976,5,biorad_96_wellplate_200ul_pcr,6,C07,1,biorad_96_wellplate_200ul_pcr,11,RAILPB03,A09,15
...
```

You can also access a template ***[here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0df680/ex.csv)***.


### Labware
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
0df680
