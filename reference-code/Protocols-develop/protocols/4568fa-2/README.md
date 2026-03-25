# FA Workflow

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
    * Normalization

## Description

This is a flexible normalization protocol a 2-fold dilution to an input desired concentration followed by sample aliquoting in triplicate. Normalization parameters should be input as a .csv file below, and should be formatted as shown in the following template **including headers line**:

```
sample number,sample name,sample concentration (<0.25 mg/ml)
1,007007009-403-1,1.569
2,007007009-403-2,0.984
3,007007009-403-3,2.128
4,007007009-403-4,2.413
5,007007009-403-5,2.303
6,007007009-403-6,1.541
7,007007009-403-7,2.404
8,007007009-403-8,2.352
9,007007009-403-9,2.763
10,007007009-403-10,1.763
11,007007009-403-11,2.094
12,007007009-403-12,0.906
13,007007009-403-13,0.715
```

You can also access this template for download [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4568fa/ex.csv)

---

### Modules
* [2x Temperature Modules (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [96-well aluminum blocks https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set]

### Labware
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml)
* [MicroAmp EnduraPlate Optical 96-Well Clear Reaction Plates with Barcode](https://www.thermofisher.com/order/catalog/product/4483352)
* [Opentrons 24 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [Eppendorf 2 mL Snapcap Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-1-5-ml-sample-vial) or equivalent
* [Opentrons 96 Filter Tip Rack 200 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 96 Filter Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)

### Pipettes
* [P300 Single-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [P20 Single-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

---

### Deck Setup
This example starting deck state shows the layout for 24 samples:  
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4568fa/deck2.png)

* green on tuberacks: starting samples at various concentrations (specified in .csv file)
* blue on reservoir A1: water
* pink on reservoir A2: blank solution
* purple on tuberack A6-C6: HS diluent

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
4568fa
