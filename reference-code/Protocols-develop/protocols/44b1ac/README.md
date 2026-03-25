# QIAseq Targeted RNAscan Panel for Illumina Instruments

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* QIAseq Targeted RNAscan Panel for Illumina Instruments

## Description
This protocol automates the QIAseq Targeted RNAscan Panel for Illumina Instruments protocol in the [QIAseq Targeted RNAscan Panel](https://www.qiagen.com/pt/products/discovery-and-translational-research/next-generation-sequencing/rna-sequencing/rna-fusions/qiaseq-targeted-rnascan-panel/?clear=true#orderinginformation) on the OT-2. The QIAseq Targeted RNAscan Panels are a complete Sample to Insight solution that applies the molecular barcode-based digital RNA sequencing strategy to quantify known and new fusion genes.

Explanation of complex parameters below:
* `Number of Samples`: The total number of DNA samples. Samples must range between 1 (minimum) and 12 (maximum).
* `Samples Labware Type`: The starting samples can be placed in either 1.5 mL tubes on the Opentrons Tube Rack OR in a 96 Well Plate.
* `P300 Single GEN2 Pipette Mount Position`: The position of the pipette, either left or right.
* `P20 Single GEN2 Pipette Mount Position`: The position of the pipette, either left or right.
* `IL-N7 Adapter Row`: Choose the row the adapters will be used from either Plates A, B, C, or D.
* `Magnetic Module Engage Height`: The height the magnets will raise on the magnetic module.
* `Wash 1 Bead Volume`: Choose the bead volume based on RNA quality.
* `Wash 2 Bead Volume`: Choose the bead volume based on RNA quality (This value is used for all subsequent bead washes). 

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Labware
* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 96 Well 100 uL PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 2 mL 96-Well Deep Well Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [Opentrons Aluminum Block Set](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)

### Pipettes
* [P300 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)
* [P20 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)

### Reagents
[QIAseq Targeted RNAscan Panel](https://www.qiagen.com/pt/products/discovery-and-translational-research/next-generation-sequencing/rna-sequencing/rna-fusions/qiaseq-targeted-rnascan-panel/?clear=true#orderinginformation)

---

### Deck Setup
* If the deck layout of a particular protocol is more or less static, it is often helpful to attach a preview of the deck layout, most descriptively generated with Labware Creator. Example:
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/44b1ac/44B1AC-layout.png)

### Reagent Setup
**Samples Setup Options (Either Tubes or Plate)**

Samples should be loaded going down the column first.
* Samples (1.5 mL Tubes): Slot 2

![Samples Tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7fc3/samples_tubes.png)

* Samples (96 Well NEST-100 uL PCR Plate): Slot 2

![Samples Plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7fc3/samples_plate.png)

* RP Primer: The protocol begins with RP Primer in position A1 of Slot 5. Further reagent swapping instructions are provided on screen through the Opentrons App as the protocol progresses.

---

### Protocol Steps

**First strand cDNA synthesis**

1. Pre-Heat Thermocycler to 65°C with lid at 103°C.
2. Pre-Cool Temperature Module to 4°C
3. Transfer 5 uL of RNA to PCR Plate on Temperature Module
4. Add 1 uL of RP Primer to Samples on PCR Plate
5. Mix by pipetting 7 times and then pause protocol to centrifuge briefly.
6. Place PCR plate in Thermocycler and click Resume.
7. Incubate at  65°C for 5 minutes and then place on temperature module for 2 minutes.
8. Briefly centrifuge and return plate to the temperature module.
9. Remove RP Primer tube and replace with First Strand Synthesis Mix. Add 4 uL of First Strand Synthesis Mix
10. Mix by pipetting 7 times and then pause protocol to centrifuge briefly.
11. Place PCR plate into the thermocycler and click resume.
12. Incubate with the following parameters: 25°C for 10 minutes, 42°C for 30 minutes, 70°C for 15 minutes, then hold at 4°C.
13. Remove place for thermocycler, briefly centrifuge and return plate to the temperature module.
14. Remove First Strand Synthesis Mix and replace with Second Strand Synthesis Mix.

**Second Strand Synthesis**

15. Add 10 uL of Second Strand Synthesis Mix to samples.
16. Mix by pipetting 7 times and then pause protocol to centrifuge briefly.
17. Place PCR plate into the thermocycler and click resume. 
18. Incubate with the following parameters: 37°C for 7 minutes, 65°C for 10 minutes, 80°C for 10 minutes, then hold at 4°C.
19. Remove PCR plate from thermocycler, briefly centrifuge and then replace on the temperature module.

**End repair/dA tailing**

20. Remove the second strange synthesis mix tube and replace with End repair/dA tailing mix in position A1 of slot 5. Also place the ERA enzyme tube in position B1.
21. Cool thermocycler to 4°C and set lid temperature to 70°C.
22. Add 20 uL of End repair/dA tailing mix to samples.
23. Add 10 uL of ERA Enzyme to the samples.
24. Pause and briefly centrifuge the plate and then place into the thermocycler. Click Resume to continue.
25. Incubate with the following parameters: 4°C for 1 minute, 20°C for 30 minutes, 65°C for 30 minutes, then hold at 4°C.
26. Remove plate from thermocycler and place on the temperature module.
27. Remove previous reagents and place the ligation mix in A1 of slot 5.
28. Place the IL-N7 adapter plate in Slot 2. Then click Resume.
29. Transfer 5 uL of IL-N7 adapter with molecular tags to each PCR well with 50 uL of reaction mixture.
30. Add 45 uL of ligation mix to each sample and mix thoroughly.
31. Incubate the ligation reaction at 20°C for 15 minutes with the lid open.

**Sample Cleanup 1**

32. Remove the PCR plate from the thermocycler and place it on the temperature module. Place a new NEST 96 Well Deep well plate on the Magnetic Module (Mag Plate).
33. Place a NEST 12 well reservoir containing Ethanol (A1) and nuclease-free water (A12) in Slot 2. Place QIAseq Beads in Slot 5 position A1.
34. Transfer 100 uL of Reaction Product to Mag Plate
35. Perform bead wash and mix thoroughly by pipetting 10 times.
36. Incubate for 5 min at room temperature.
37. Engage magnetic module for 15 minutes and then remove supernantant.
38. Completely remove residual supernatant with the P20 pipette.
39. Perform an ethanol wash with 260 uL.
40. Remove supernatant completely.
41. Repeat steps 39 and 40.
42. Delay for 10 minutes to dry beads.
43. Add 52 uL of Nuclease-Free Water to Elute DNA
44. Engage magnetic module for 5 minutes to separate the beads.
45. Place a new NEST 96 Well Deep well plate in slot 4 (intermediate plate). Ensure there is enough volume of QIAseq beads.
46. Transfer 50 uL of sample to new intermediate plate.
47. Perform bead wash and mix thoroughly by pipetting 10 times.
48. Incubate for 5 min at room temperature.
49. Remove old Mag Plate and place the new Intermediate plate on the magnetic module. The intermediate plate will now be referred to as the Mag Plate.
50. Engage magnetic module for 10 minutes to separate beads.
51. Remove and discard supernatant.
52. Perform a 200 uL ethanol wash and remove and discard supernatant.
53. Repeat step 52.
54. Completely remove residual supernatant.
55. Dry beads for 5 minutes while magnets are engaged.
56. Add 12.4 uL of Nuclease-Free Water to Elute DNA
57. Please remove the old PCR plate on the temperature module and place a new PCR plate. Then click Resume to continue.
58. Transfer 10.4 uL of supernatant to new PCR plate.

**SPE Target Enrichment**

59. Pause and **manually** add SPE Reaction Mix to each sample and then place the PCR plate in the thermocycler. Click Resume when ready.
60. Incubate with the following parameters: 95°C for 15 minutes, 95°C for 15 seconds and 68°C for 10 minutes (8 cycles), 72°C for 5 minutes, then hold at 4°C.
61. Remove the PCR plate from the thermocycler and place on temperature module.

**Sample Cleanup 2**

62. Place a new deep well plate onto the magnetic module.
63. Add 30 uL of nuclease free water to bring volume to 50 uL.
64. Transfer samples to new mag plate.
65. Perform bead wash and mix thoroughly by pipetting 10 times.
66. Incubate for 5 min at room temperature.
67. Engage magnetic module for 5 minutes and remove supernatant.
68. Perform a 200 uL ethanol wash and remove supernatant.
69. Repeat step 68.
70. Dry beads for 5 minutes while magnets are engaged.
71. Add 15.4 uL of Nuclease-Free Water to Elute DNA.
72. Place a new PCR plate on the temperature module.
73. Transfer 13.4 uL of Supernatant to PCR Plate.

**Universal PCR Amplification**

74. **Manually** add the Universal PCR mix to the samples on the PCR plate. Then place plate in the thermocycler.
75. Incubate with the following parameters: 95°C for 15 minutes, 95°C for 15 seconds and 60°C for 2 minutes (25 cycles), 72°C for 5 minutes, then hold at 4°C.
76. Remove PCR plate from thermocycler and plate on the temperature module.

**Sample Cleanup 3**

77. Place a new deep well plate on the magnetic module. Ensure ethanol and QIAseq bead volumes are adequate for cleanup.
78. Add 30 uL of nuclease free water to bring volume to 50 uL.
79. Transfer samples to new mag plate.
80. Perform bead wash and mix thoroughly by pipetting 10 times.
81. Incubate for 5 min at room temperature.
82. Engage magnetic module for 5 minutes and remove supernatant.
83. Perform a 200 uL ethanol wash and remove supernatant.
84. Repeat step 68.
85. Dry beads for 5 minutes while magnets are engaged.
86. Add 25 uL of Nuclease-Free Water to Elute DNA.
87. Delay for 5 minutes for solution to clear
88. Place a new PCR plate on the temperature module.
89. Transfer 21 uL of Supernatant to PCR Plate.
90. Protocol Completed! Proceed to library quantification.

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
44b1ac