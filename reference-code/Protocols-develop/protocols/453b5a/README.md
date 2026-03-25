# Nucleic Acid Purification and PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs a custom nucleic acid purification and PCR preparation on a PCR plate mounted on an Opentrons temperature module with aluminum block insert. The final step of the protocol is to transfer various PCR mixes in 1.5ml tubes to corresponding tubes. The source mix tubes and destination wells in the PCR plate should be specified in `.csv` format as in the following example:

```
mix tube,PCR plate start well,PCR plate end well
A1,A1,H2
B1,A3,H6
C1,A7,H8
D1,A9,H12
```

You can also download a template for this input [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/453b5a/csv_temp.csv), edit in a spreadsheet editor like Google Sheets, MS Excel, or Apple Numbers, export as a `.csv` file, and upload below as the `.csv file to specify PCR mix destinations` parameter.

The user is prompted to refill tipracks when necessary for both the P20 single-channel and P300 multi-channel pipettes.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons temperature module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [96-well aluminum block insert](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) holding [Biozym 96-well PCR plate #712547 200µl](https://www.biozym.com/DesktopModules/WebShop/shopdisplayproducts.aspx?id=4652&cat=Low+Profile)
* Custom 24-cuvette racks for Greiner Bio-One Vacuette tubes (1-4)
* [Opentrons 4-in-1 tuberack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 4x6 insert for [Eppendorf 1.5 mL Safe-Lock Snapcap tubes](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Tubes-44515/Eppendorf-Safe-Lock-Tubes-PF-8863.html)
* [USA Scientific 12-channel reservoir 22ml #1061-8150](https://www.usascientific.com/12-channel-automation-reservoir/p/1061-8150)
* [Opentrons P20 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons P300 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 20µl and 50/300µl tipracks](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

blood collection tube racks (slots 7, 8, 10, 11):
* tubes 1-24: slot 7
* tubes 25-48: slot 8
* tubes 49-72: slot 10
* tubes 73-96: slot 11

12-channel reservoir (slot 1)
* channel 1: concentration dilution
* channel 2: buffer B
* channels 3-5: buffer C
* channels 9-12: liquid waste (loaded empty)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the mount side for your P1000 single-channel pipette, the number of capsules to fill, and the volume to fill each capsule (in ul).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
453b5a
