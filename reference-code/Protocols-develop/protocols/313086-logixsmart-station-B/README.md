# Logix Smart Nasopharyngeal/Saliva Covid-19 PCR Prep (Station B)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Covid Workstation
	* qPCR Setup

## Description
Links:  
* [Logix Smart Nasopharyngeal Covid-19 Plating (Station A)](./313086)
* [Logix Smart Nasopharyngeal/Saliva Covid-19 PCR Prep (Station B)](./313086-logixsmart-station-B)

This protocol performs PCR prep in a NEST 96-well PCR plate. Samples with buffer pre-added should be arranged in a NEST 96-deepwell, and mastermix and controls should be loaded in 1.5ml microcentrifuge tubes in the Opentrons 4x6 tuberack. The transfer order is as shown below:  
![order](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/demo/order.png)

---

### Labware
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [Opentrons 24 tuberack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [NEST 1.5 mL Microcentrifuge Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons 10µl tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

### Pipettes
* [P10 Single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [P10 Multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

### Reagents
* [Logix Smart Nasopharyngeal Covid-19 Kit](https://codiagnostics.com/products/diagnostic-solutions/logix-smart-covid19/)

---

### Deck Setup
* green: mastermix
* pink: positive control
* purple: negative control  
* blue: starting samples
![deck setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/313086-station-C/deck_setup2.png)

---

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
313086
