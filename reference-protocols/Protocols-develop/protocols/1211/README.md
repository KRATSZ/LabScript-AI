# Cherrypicking

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking


## Description
With this protocol, your robot can perform multiple well-to-well liquid transfers using a single-channel pipette by parsing through a user-defined .csv file.

The .csv file should be formatted as shown in the example below, **including headers**:

```
Source Labware,Source Slot,Source Well,Source Aspiration Height Above Bottom (in mm),Dest Labware,Dest Slot,Dest Well,Volume (in ul)
agilent_1_reservoir_290ml,1,A1,1,nest_96_wellplate_100ul_pcr_full_skirt,4,A11,1
nest_12_reservoir_15ml,2,A1,1,nest_96_wellplate_2ml_deep,5,A5,3
nest_1_reservoir_195ml,3,A1,1,nest_96_wellplate_2ml_deep,5,H12,7
```

All available empty slots will be filled with the necessary tipracks, and the user will be prompted to refill the tipracks if all are emptied in the middle of the protocol.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
1211
